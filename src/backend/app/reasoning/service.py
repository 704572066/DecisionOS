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
from app.reasoning.llm_constraint_compiler import (
    LLMConstraintCompilerBackend,
)
from app.reasoning.models import (
    ReasoningDiagnostics,
    ReasoningResult,
)
from app.runtime.models import RuntimeState


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
                diagnostics=diagnostics,
            )

        #
        # ------------------------------------------------------------
        # 4. Unified ReasoningResult
        # ------------------------------------------------------------
        #
        return ReasoningResult(
            meetingId=context.meetingId,
            contextId=context.contextId,
            projectId=context.projectId,
            findings=finding_set.findings,
            constraints=compilation.constraints,
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