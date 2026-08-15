from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.reasoning.context import EvaluationKnowledge


@dataclass
class KnowledgeEligibility:
    knowledgeId: str
    eligible: bool
    reason: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


class KnowledgeCompilationGovernance:
    """
    Decide whether retrieved knowledge may be compiled into an
    executable EvaluationConstraint.

    This layer governs knowledge ROLE, not business semantics.

    Current MVP policy:
        policy -> eligible
        other knowledge types -> evidence/context only

    Future extensions may use:
        attributes.knowledgeRole
        attributes.binding
        approval state
        governance metadata
    """

    ELIGIBLE_SOURCE_TYPES = {
        "policy",
    }

    def evaluate(
        self,
        knowledge: EvaluationKnowledge,
    ) -> KnowledgeEligibility:
        source_type = (
            knowledge.sourceType
            or ""
        ).strip().lower()

        #
        # Future-proof explicit metadata override.
        #
        attributes = dict(
            knowledge.attributes
            or {}
        )

        knowledge_role = str(
            attributes.get("knowledgeRole")
            or ""
        ).strip().lower()

        binding = attributes.get("binding")

        #
        # Explicit normative + binding knowledge may become executable,
        # regardless of its storage/source category.
        #
        if (
            knowledge_role == "normative"
            and binding is True
        ):
            return KnowledgeEligibility(
                knowledgeId=knowledge.id,
                eligible=True,
                reason="explicit_normative_binding",
            )

        #
        # MVP default:
        # policy sources are considered normative.
        #
        if source_type in self.ELIGIBLE_SOURCE_TYPES:
            return KnowledgeEligibility(
                knowledgeId=knowledge.id,
                eligible=True,
                reason="eligible_source_type",
            )

        return KnowledgeEligibility(
            knowledgeId=knowledge.id,
            eligible=False,
            reason="non_normative_knowledge",
            metadata={
                "sourceType": knowledge.sourceType,
                "knowledgeRole": knowledge_role,
                "binding": binding,
            },
        )

    def partition(
        self,
        knowledge_items: list[EvaluationKnowledge],
    ) -> tuple[
        list[EvaluationKnowledge],
        list[KnowledgeEligibility],
    ]:
        eligible: list[EvaluationKnowledge] = []
        skipped: list[KnowledgeEligibility] = []

        for knowledge in knowledge_items:
            result = self.evaluate(
                knowledge
            )

            if result.eligible:
                eligible.append(
                    knowledge
                )
            else:
                skipped.append(
                    result
                )

        return eligible, skipped


knowledge_compilation_governance = (
    KnowledgeCompilationGovernance()
)