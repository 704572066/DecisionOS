from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from app.reasoning.context import (
    EvaluationConstraint,
    EvaluationContext,
    EvaluationKnowledge,
)
from app.reasoning.constraint_validator import (
    ConstraintValidator,
    constraint_validator,
)
from app.reasoning.knowledge_governance import (
    KnowledgeCompilationGovernance,
    knowledge_compilation_governance,
)


@dataclass
class ConstraintCompilationResult:
    constraints: list[EvaluationConstraint] = field(
        default_factory=list
    )

    rejected: list[dict[str, Any]] = field(
        default_factory=list
    )

    diagnostics: dict[str, Any] = field(
        default_factory=dict
    )


class ConstraintCompilerBackend(ABC):
    """
    Pluggable semantic compilation backend.

    The backend converts eligible enterprise knowledge into the
    generic EvaluationConstraint DSL.
    """

    @abstractmethod
    async def compile_knowledge(
        self,
        *,
        knowledge: EvaluationKnowledge,
        context: EvaluationContext,
    ) -> list[EvaluationConstraint]:
        raise NotImplementedError


class NullConstraintCompilerBackend(
    ConstraintCompilerBackend
):
    """
    Safe default backend.

    Performs no semantic inference.
    """

    async def compile_knowledge(
        self,
        *,
        knowledge: EvaluationKnowledge,
        context: EvaluationContext,
    ) -> list[EvaluationConstraint]:
        return []


class ConstraintCompiler:
    """
    Constraint compilation orchestration layer.

    Pipeline:

        EvaluationKnowledge[]
                ↓
        KnowledgeCompilationGovernance
                ↓
        eligible knowledge only
                ↓
        ConstraintCompilerBackend
                ↓
        EvaluationConstraint[]
                ↓
        ConstraintValidator
                ↓
        valid constraints

    Non-normative knowledge remains available in EvaluationContext
    for evidence / precedent / recommendation, but is not compiled
    into executable constraints.
    """

    def __init__(
        self,
        backend: ConstraintCompilerBackend | None = None,
        validator: ConstraintValidator | None = None,
        governance: KnowledgeCompilationGovernance | None = None,
    ) -> None:
        self.backend = (
            backend
            if backend is not None
            else NullConstraintCompilerBackend()
        )

        self.validator = (
            validator
            if validator is not None
            else constraint_validator
        )

        self.governance = (
            governance
            if governance is not None
            else knowledge_compilation_governance
        )

    async def compile(
        self,
        context: EvaluationContext,
    ) -> ConstraintCompilationResult:
        compiled: list[EvaluationConstraint] = []

        backend_errors: list[dict[str, Any]] = []

        #
        # ------------------------------------------------------------
        # 1. Knowledge governance
        # ------------------------------------------------------------
        #
        eligible_knowledge, skipped_knowledge = (
            self.governance.partition(
                context.knowledge
            )
        )

        attempted = 0

        #
        # ------------------------------------------------------------
        # 2. Compile eligible knowledge only
        # ------------------------------------------------------------
        #
        for knowledge in eligible_knowledge:
            attempted += 1

            try:
                constraints = (
                    await self.backend.compile_knowledge(
                        knowledge=knowledge,
                        context=context,
                    )
                )

                compiled.extend(
                    constraints
                )

            except Exception as exc:
                backend_errors.append(
                    {
                        "knowledgeId": knowledge.id,
                        "error": str(exc),
                    }
                )

        #
        # ------------------------------------------------------------
        # 3. Structural validation
        # ------------------------------------------------------------
        #
        valid_constraints, rejected = (
            self.validator.validate_many(
                compiled
            )
        )

        #
        # ------------------------------------------------------------
        # 4. Diagnostics
        # ------------------------------------------------------------
        #
        skipped_payload = [
            {
                "knowledgeId": item.knowledgeId,
                "reason": item.reason,
                "metadata": dict(
                    item.metadata
                    or {}
                ),
            }
            for item in skipped_knowledge
        ]

        return ConstraintCompilationResult(
            constraints=valid_constraints,

            rejected=rejected,

            diagnostics={
                #
                # Input
                #
                "knowledgeCount": len(
                    context.knowledge
                ),

                #
                # Governance
                #
                "eligibleKnowledgeCount": len(
                    eligible_knowledge
                ),

                "skippedKnowledgeCount": len(
                    skipped_knowledge
                ),

                "skippedKnowledge": (
                    skipped_payload
                ),

                #
                # Compilation
                #
                "attemptedKnowledgeCount": attempted,

                "compiledConstraintCount": len(
                    compiled
                ),

                #
                # Validation
                #
                "validConstraintCount": len(
                    valid_constraints
                ),

                "rejectedConstraintCount": len(
                    rejected
                ),

                #
                # Backend
                #
                "backendErrorCount": len(
                    backend_errors
                ),

                "backendErrors": backend_errors,

                "backend": type(
                    self.backend
                ).__name__,

                #
                # Governance implementation
                #
                "governance": type(
                    self.governance
                ).__name__,
            },
        )


constraint_compiler = ConstraintCompiler()