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

    The backend converts enterprise knowledge into the generic
    EvaluationConstraint DSL.

    Implementations may use:
    - LLM
    - rule service
    - external policy engine
    - precompiled constraints

    Business semantics belong to the backend input/interpretation,
    not to ConstraintCompiler itself.
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

    It deliberately performs no semantic inference.
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

        EvaluationKnowledge
                ↓
        semantic compiler backend
                ↓
        EvaluationConstraint[]
                ↓
        ConstraintValidator
                ↓
        valid constraints

    This layer contains no enterprise-specific interpretation.
    """

    def __init__(
        self,
        backend: ConstraintCompilerBackend | None = None,
        validator: ConstraintValidator | None = None,
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

    async def compile(
        self,
        context: EvaluationContext,
    ) -> ConstraintCompilationResult:
        compiled: list[EvaluationConstraint] = []

        backend_errors: list[dict[str, Any]] = []

        attempted = 0

        for knowledge in context.knowledge:
            attempted += 1

            try:
                constraints = (
                    await self.backend.compile_knowledge(
                        knowledge=knowledge,
                        context=context,
                    )
                )

                compiled.extend(constraints)

            except Exception as exc:
                backend_errors.append(
                    {
                        "knowledgeId": knowledge.id,
                        "error": str(exc),
                    }
                )

        valid_constraints, rejected = (
            self.validator.validate_many(compiled)
        )

        return ConstraintCompilationResult(
            constraints=valid_constraints,
            rejected=rejected,
            diagnostics={
                "knowledgeCount": len(context.knowledge),
                "attemptedKnowledgeCount": attempted,
                "compiledConstraintCount": len(compiled),
                "validConstraintCount": len(
                    valid_constraints
                ),
                "rejectedConstraintCount": len(
                    rejected
                ),
                "backendErrorCount": len(
                    backend_errors
                ),
                "backendErrors": backend_errors,
                "backend": type(
                    self.backend
                ).__name__,
            },
        )


constraint_compiler = ConstraintCompiler()