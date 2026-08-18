from __future__ import annotations

from typing import Any

from app.reasoning.constraint_compiler import (
    ConstraintCompiler,
)
from app.reasoning.context_builder import (
    EvaluationContextBuilder,
    evaluation_context_builder,
)
from app.reasoning.finding_set_evaluator import (
    FindingSetEvaluator,
)
from app.reasoning.general import (
    GeneralReasoner,
    GeneralReasoningContextBuilder,
    general_reasoner,
    general_reasoning_context_builder,
)
from app.reasoning.shared_finding_merger import (
    SharedFindingMerger,
    shared_finding_merger,
)
from app.reasoning.llm_constraint_compiler import (
    LLMConstraintCompilerBackend,
)
from app.reasoning.models import (
    ReasoningDiagnostics,
    ReasoningResult,
)
from app.reasoning.normative_boundary_guard import (
    NormativeBoundaryGuard,
    normative_boundary_guard,
)
from app.reasoning.recommendation_set_evaluator import (
    RecommendationSetEvaluator,
)
from app.runtime.models import RuntimeState
from app.intervention.policy import (
    InterventionPolicy,
    intervention_policy,
)
from app.intervention.delivery import active_intervention_delivery
from app.reasoning.snapshot_store import (
    ReasoningSnapshotStore,
    reasoning_snapshot_store,
)


class ReasoningService:
    """
    Runtime reasoning orchestration service.

    Pipeline:

        RuntimeState
            ↓
        EvaluationContextBuilder
            ↓
        EvaluationContext
            ↓
        ConstraintCompiler
            ↓
        EvaluationConstraint[]
            ↓
        FindingSetEvaluator
            ↓
        FindingSet
            ↓
        ReasoningResult

    Responsibilities:
    - orchestrate already-existing reasoning components
    - preserve diagnostics across compilation/evaluation stages
    - provide one stable RuntimeState -> ReasoningResult entry point

    Non-responsibilities:
    - retrieve RuntimeState from database
    - modify RuntimeState
    - modify DecisionBoard
    - interpret policies directly
    - implement business rules
    """

    def __init__(
        self,
        *,
        context_builder: EvaluationContextBuilder | None = None,
        compiler: ConstraintCompiler | None = None,
        finding_evaluator: FindingSetEvaluator | None = None,
        general_context_builder: GeneralReasoningContextBuilder | None = None,
        general_reasoner_instance: GeneralReasoner | None = None,
        finding_merger: SharedFindingMerger | None = None,
        normative_guard: NormativeBoundaryGuard | None = None,
        recommendation_evaluator: RecommendationSetEvaluator | None = None,
        intervention_policy_instance: InterventionPolicy | None = None,
        snapshot_store: ReasoningSnapshotStore | None = None,
    ) -> None:
        self.context_builder = (
            context_builder
            if context_builder is not None
            else evaluation_context_builder
        )

        self.compiler = (
            compiler
            if compiler is not None
            else ConstraintCompiler(
                backend=LLMConstraintCompilerBackend()
            )
        )

        #
        # IMPORTANT:
        #
        # FindingSetEvaluator owns its repository/lifecycle state.
        # Therefore one ReasoningService instance should be reused,
        # rather than recreated for every request.
        #
        self.finding_evaluator = (
            finding_evaluator
            if finding_evaluator is not None
            else FindingSetEvaluator()
        )

        self.general_context_builder = (
            general_context_builder
            if general_context_builder is not None
            else general_reasoning_context_builder
        )

        self.general_reasoner = (
            general_reasoner_instance
            if general_reasoner_instance is not None
            else general_reasoner
        )

        self.finding_merger = (
            finding_merger
            if finding_merger is not None
            else shared_finding_merger
        )

        self.normative_guard = (
            normative_guard
            if normative_guard is not None
            else normative_boundary_guard
        )

        self.recommendation_evaluator = (
            recommendation_evaluator
            if recommendation_evaluator is not None
            else RecommendationSetEvaluator()
        )

        self.intervention_policy = (
            intervention_policy_instance
            if intervention_policy_instance is not None
            else intervention_policy
        )

        self.snapshot_store = (
            snapshot_store
            if snapshot_store is not None
            else reasoning_snapshot_store
        )

    async def get_or_reason(
        self,
        state: RuntimeState,
        *,
        force: bool = False,
    ) -> ReasoningResult:
        """Return the shared reasoning snapshot for this RuntimeState.

        Lifecycle-aware reasoning must execute at most once for one
        RuntimeState revision. All interaction surfaces consume the same
        result. ``force`` is reserved for an explicit reasoning refresh.
        """
        if not force:
            cached = self.snapshot_store.get(state)
            if cached is not None:
                return cached

        async with self.snapshot_store.lock(state.meetingId):
            if not force:
                cached = self.snapshot_store.get(state)
                if cached is not None:
                    return cached

            result = await self.reason(state)
            return self.snapshot_store.put(state, result)

    async def reason(
        self,
        state: RuntimeState,
    ) -> ReasoningResult:
        diagnostics = ReasoningDiagnostics()

        #
        # ------------------------------------------------------------
        # 1. RuntimeState -> EvaluationContext
        # ------------------------------------------------------------
        #
        try:
            context = self.context_builder.build(
                state
            )

            diagnostics.evaluationContextBuilt = True

            diagnostics.knowledgeCount = len(
                context.knowledge
            )

        except Exception as exc:
            diagnostics.evaluationContextBuilt = False

            diagnostics.evaluationErrors.append(
                f"context_builder: {exc}"
            )

            return ReasoningResult(
                meetingId=state.meetingId,
                contextId=state.contextId,
                projectId=state.projectId,
                findings=[],
                constraints=[],
                recommendations=[],
                diagnostics=diagnostics,
            )

        #
        # ------------------------------------------------------------
        # 2. EvaluationKnowledge -> EvaluationConstraint[]
        # ------------------------------------------------------------
        #
        try:
            compilation = await self.compiler.compile(
                context
            )

            diagnostics.compiledConstraintCount = len(
                compilation.constraints
            )

            diagnostics.rejectedConstraintCount = len(
                compilation.rejected
            )

            backend_errors = list(
                compilation.diagnostics.get(
                    "backendErrors"
                )
                or []
            )

            for error in backend_errors:
                diagnostics.compilationErrors.append(
                    self._format_compilation_error(
                        error
                    )
                )

            diagnostics.metadata[
                "constraintCompilation"
            ] = dict(
                compilation.diagnostics
            )

        except Exception as exc:
            diagnostics.compilationErrors.append(
                f"constraint_compiler: {exc}"
            )

            return ReasoningResult(
                meetingId=context.meetingId,
                contextId=context.contextId,
                projectId=context.projectId,
                findings=[],
                constraints=[],
                recommendations=[],
                diagnostics=diagnostics,
            )

        #
        # ------------------------------------------------------------
        # 3. EvaluationConstraint[] -> FindingSet
        # ------------------------------------------------------------
        #
        try:
            finding_set = (
                self.finding_evaluator.evaluate(
                    context,
                    compilation.constraints,
                )
            )

            finding_diagnostics = dict(
                finding_set.diagnostics
                or {}
            )

            diagnostics.triggeredFindingCount = int(
                finding_diagnostics.get(
                    "triggeredCount",
                    0,
                )
            )

            diagnostics.activeFindingCount = int(
                finding_diagnostics.get(
                    "activeFindingCount",
                    0,
                )
            )

            diagnostics.resolvedFindingCount = int(
                finding_diagnostics.get(
                    "resolvedCount",
                    0,
                )
            )

            evaluation_errors = list(
                finding_diagnostics.get(
                    "evaluationErrors"
                )
                or []
            )

            for error in evaluation_errors:
                diagnostics.evaluationErrors.append(
                    self._format_evaluation_error(
                        error
                    )
                )

            diagnostics.metadata[
                "findingEvaluation"
            ] = finding_diagnostics

        except Exception as exc:
            diagnostics.evaluationErrors.append(
                f"finding_evaluator: {exc}"
            )

            return ReasoningResult(
                meetingId=context.meetingId,
                contextId=context.contextId,
                projectId=context.projectId,
                findings=[],
                constraints=compilation.constraints,
                recommendations=[],
                diagnostics=diagnostics,
            )

        #
        # ------------------------------------------------------------
        # 4. RuntimeState + Policy Findings -> General Findings
        # ------------------------------------------------------------
        #
        general_findings = []

        try:
            general_context = (
                self.general_context_builder.build(
                    state,
                    policy_findings=finding_set.findings,
                )
            )

            general_result = (
                await self.general_reasoner.reason(
                    general_context
                )
            )

            general_findings = list(
                general_result.findings
            )

            diagnostics.generalFindingCount = len(
                general_findings
            )

            diagnostics.metadata[
                "generalReasoning"
            ] = general_result.diagnostics.model_dump(
                mode="json"
            )

        except Exception as exc:
            # General reasoning is additive. Enterprise-policy reasoning
            # remains authoritative even when General Reasoner fails.
            diagnostics.evaluationErrors.append(
                f"general_reasoner: {exc}"
            )

            diagnostics.metadata[
                "generalReasoning"
            ] = {
                "error": str(exc),
            }

        #
        # ------------------------------------------------------------
        # 5. Normative Boundary Guard
        # ------------------------------------------------------------
        #
        # General Reasoner may discuss enterprise knowledge, but compiled
        # EvaluationConstraint semantics remain authoritative for normative
        # applicability. This deterministic guard prevents General Reasoner
        # from turning `> 10` into `>= 10`, or otherwise inventing policy
        # requirements whose structured precondition is false.
        #
        normative_suppressed_count = 0

        try:
            normative_result = self.normative_guard.apply(
                context=context,
                constraints=compilation.constraints,
                enterprise_findings=finding_set.findings,
                general_findings=general_findings,
            )

            general_findings = list(
                normative_result.findings
            )

            normative_diagnostics = dict(
                normative_result.diagnostics
                or {}
            )

            normative_suppressed_count = int(
                normative_diagnostics.get(
                    "suppressedGeneralFindingCount",
                    0,
                )
            )

            diagnostics.normativeSuppressedGeneralFindingCount = (
                normative_suppressed_count
            )

            diagnostics.metadata[
                "normativeBoundaryGuard"
            ] = normative_diagnostics

        except Exception as exc:
            # Fail open for additive General reasoning. Enterprise findings
            # remain authoritative and the error is visible in diagnostics.
            diagnostics.evaluationErrors.append(
                f"normative_boundary_guard: {exc}"
            )

            diagnostics.metadata[
                "normativeBoundaryGuard"
            ] = {
                "error": str(exc),
            }

        #
        # ------------------------------------------------------------
        # 6. Enterprise Findings + General Findings -> Shared Findings
        # ------------------------------------------------------------
        #
        try:
            shared_finding_set = (
                self.finding_merger.merge(
                    meeting_id=context.meetingId,
                    context_id=context.contextId,
                    enterprise_findings=(
                        finding_set.findings
                    ),
                    general_findings=(
                        general_findings
                    ),
                )
            )

            merge_diagnostics = dict(
                shared_finding_set.diagnostics
                or {}
            )

            diagnostics.enterpriseFindingCount = len(
                finding_set.findings
            )
            diagnostics.mergedFindingCount = len(
                shared_finding_set.findings
            )
            diagnostics.suppressedGeneralFindingCount = (
                normative_suppressed_count
                + int(
                    merge_diagnostics.get(
                        "suppressedGeneralFindingCount",
                        0,
                    )
                )
            )

            diagnostics.activeFindingCount = sum(
                1
                for item in shared_finding_set.findings
                if item.status != "resolved"
            )

            diagnostics.metadata[
                "sharedFindingMerge"
            ] = merge_diagnostics

        except Exception as exc:
            diagnostics.evaluationErrors.append(
                f"shared_finding_merger: {exc}"
            )

            shared_finding_set = finding_set
            diagnostics.enterpriseFindingCount = len(
                finding_set.findings
            )
            diagnostics.mergedFindingCount = len(
                finding_set.findings
            )

        #
        # ------------------------------------------------------------
        # 7. Shared FindingSet -> RecommendationSet
        # ------------------------------------------------------------
        #
        try:
            recommendation_set = (
                self.recommendation_evaluator.evaluate(
                    meeting_id=context.meetingId,
                    context_id=context.contextId,
                    findings=shared_finding_set.findings,
                )
            )

            recommendation_diagnostics = dict(
                recommendation_set.diagnostics
                or {}
            )

            diagnostics.generatedRecommendationCount = int(
                recommendation_diagnostics.get(
                    "generatedCount",
                    0,
                )
            )

            diagnostics.activeRecommendationCount = int(
                recommendation_diagnostics.get(
                    "activeRecommendationCount",
                    0,
                )
            )

            diagnostics.obsoleteRecommendationCount = int(
                recommendation_diagnostics.get(
                    "obsoleteCount",
                    0,
                )
            )

            diagnostics.metadata[
                "recommendationEvaluation"
            ] = recommendation_diagnostics

        except Exception as exc:
            diagnostics.evaluationErrors.append(
                f"recommendation_evaluator: {exc}"
            )

            return ReasoningResult(
                meetingId=context.meetingId,
                contextId=context.contextId,
                projectId=context.projectId,
                findings=shared_finding_set.findings,
                constraints=compilation.constraints,
                recommendations=[],
                diagnostics=diagnostics,
            )

        #
        # ------------------------------------------------------------
        # 8. Findings + Recommendations -> Intervention Decisions
        # ------------------------------------------------------------
        #
        interventions = []

        try:
            intervention_set = self.intervention_policy.evaluate(
                state=state,
                findings=shared_finding_set.findings,
                recommendations=recommendation_set.recommendations,
            )

            interventions = list(intervention_set.decisions)
            intervention_diagnostics = dict(
                intervention_set.diagnostics or {}
            )

            diagnostics.interventionCount = len(interventions)
            diagnostics.interruptInterventionCount = int(
                intervention_diagnostics.get("interruptCount", 0)
            )
            diagnostics.surfaceInterventionCount = int(
                intervention_diagnostics.get("surfaceCount", 0)
            )
            diagnostics.silentInterventionCount = int(
                intervention_diagnostics.get("silentCount", 0)
            )
            diagnostics.metadata["interventionEvaluation"] = {
                **intervention_diagnostics,
                "highestLevel": intervention_set.highestLevel,
            }

            # Delivery is downstream attention infrastructure. Failures are
            # observable but must never invalidate the reasoning result.
            try:
                diagnostics.metadata["interventionDelivery"] = (
                    await active_intervention_delivery.deliver(interventions)
                )
            except Exception as delivery_exc:
                diagnostics.metadata["interventionDelivery"] = {
                    "error": str(delivery_exc),
                }

        except Exception as exc:
            # Intervention policy is presentation/attention governance.
            # It must never break the underlying reasoning result.
            diagnostics.evaluationErrors.append(
                f"intervention_policy: {exc}"
            )
            diagnostics.metadata["interventionEvaluation"] = {
                "error": str(exc),
            }

        #
        # ------------------------------------------------------------
        # 9. Unified ReasoningResult
        # ------------------------------------------------------------
        #
        return ReasoningResult(
            meetingId=context.meetingId,
            contextId=context.contextId,
            projectId=context.projectId,
            findings=shared_finding_set.findings,
            constraints=compilation.constraints,
            recommendations=(
                recommendation_set.recommendations
            ),
            interventions=interventions,
            diagnostics=diagnostics,
        )

    @staticmethod
    def _format_compilation_error(
        error: Any,
    ) -> str:
        if isinstance(
            error,
            dict,
        ):
            knowledge_id = str(
                error.get("knowledgeId")
                or ""
            )

            message = str(
                error.get("error")
                or error
            )

            if knowledge_id:
                return (
                    f"{knowledge_id}: {message}"
                )

            return message

        return str(error)

    @staticmethod
    def _format_evaluation_error(
        error: Any,
    ) -> str:
        if isinstance(
            error,
            dict,
        ):
            constraint_id = str(
                error.get("constraintId")
                or ""
            )

            message = str(
                error.get("error")
                or error
            )

            if constraint_id:
                return (
                    f"{constraint_id}: {message}"
                )

            return message

        return str(error)


#
# Application-level singleton.
#
# This is important because FindingSetEvaluator currently owns
# an in-memory meeting-scoped FindingRepository.
#
# Recreating ReasoningService for each call would lose Finding lifecycle:
#
# OPEN -> RESOLVED -> REOPEN
#
reasoning_service = ReasoningService()
