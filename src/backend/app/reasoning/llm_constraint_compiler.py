from __future__ import annotations

import json
import logging
from typing import Any

from pydantic import BaseModel, Field

from app.intelligence.llm import llm_provider
from app.reasoning.constraint_compiler import (
    ConstraintCompilerBackend,
)
from app.reasoning.context import (
    EvaluationConstraint,
    EvaluationContext,
    EvaluationKnowledge,
)


logger = logging.getLogger(
    "decisionos.reasoning.constraint_compiler"
)


class ConstraintCompilationEnvelope(BaseModel):
    constraints: list[EvaluationConstraint] = Field(
        default_factory=list
    )


SYSTEM_PROMPT = """
You are the Constraint Compiler for DecisionOS.

Your job is to translate enterprise knowledge into a generic,
machine-executable constraint DSL.

You perform SEMANTIC COMPILATION only.

You do NOT:
- make business decisions
- invent enterprise policies
- invent thresholds
- invent facts
- evaluate whether a constraint is currently satisfied
- generate recommendations
- generate findings
- use outside knowledge

======================================================================
SOURCE OF TRUTH
======================================================================

The enterprise knowledge supplied by the user is authoritative.

Compile only constraints that are explicitly supported by that
knowledge.

Never invent a rule merely because it is common business practice.

If the supplied knowledge does not contain a machine-executable
constraint, return:

{
  "constraints": []
}

======================================================================
AVAILABLE RUNTIME VOCABULARY
======================================================================

The user message may contain existing semanticSubjects and
decisionSubjects.

Use them as vocabulary/context when selecting domain and subject names.

Prefer an existing field name when the knowledge clearly refers to the
same concept.

Do NOT create a mapping based only on superficial keyword similarity.

If no existing field is appropriate, you may create a concise,
stable camelCase semantic field name that accurately represents the
concept expressed by the knowledge.

======================================================================
POLICY SCOPE VS RUNTIME CONTEXT
======================================================================

Runtime semanticSubjects and decisionSubjects are vocabulary/context only.

Never infer policy scope from the actor, role, status, or current value of
a runtime subject unless the enterprise knowledge explicitly states that
scope.

Example:

Knowledge:
"When X exceeds Y, Z must be evaluated."

Runtime context happens to contain:
actor=customer for X.

Do NOT conclude that the policy applies only to customer-owned X.

If the policy does not explicitly restrict a participant:
actor = ""

Likewise, do not choose semantic_state merely because the matching vocabulary
currently appears there.

Use subjectSource="either" when the policy itself does not explicitly limit
the rule to participant positions or final decision state.

======================================================================
CONSTRAINT STRUCTURE
======================================================================

Each constraint must conform to this conceptual structure:

{
  "id": "stable constraint id",
  "domain": "semantic domain",
  "subject": "field being evaluated",
  "subjectSource": "semantic_state | decision_state | either",
  "actor": "",
  "operator": "...",
  "expectedValue": null,
  "operand": null,
  "findingType": "risk | conflict | gap | dependency | deviation",
  "severity": "low | medium | high | critical",
  "evaluationMode": "on_match | on_mismatch",
  "title": "",
  "description": "",
  "sourceIds": [],
  "attributes": {}
}

======================================================================
OPERATORS
======================================================================

Allowed operators:

=
!=
>
>=
<
<=
in
not_in
exists
missing
requires
depends_on
conflicts_with

Comparison operators compare the runtime value with expectedValue.

exists / missing operate on existence and therefore expectedValue
must be null.


======================================================================
EVALUATION MODE
======================================================================

Use:

on_mismatch

when the rule describes a condition that MUST hold.

Example abstract form:

    X must be >= Y

The finding is emitted when that requirement is violated.

Use:

on_match

when the rule describes a trigger condition.

Example abstract form:

    when X > Y, another condition/action/dependency is required

The primary condition is the trigger.

======================================================================
OPERAND
======================================================================

Use operand when the rule relates the primary condition to another
required/conflicting/dependent condition.

The operand must preserve the exact semantic requirement of the policy.

Do not weaken or substitute the required concept.

For example, if knowledge says:

"X requires Y to be evaluated"

then an operand meaning merely:

"Y exists"

is NOT equivalent.

Represent the evaluation/assessment itself as the operand subject, using a
stable semantic field name if necessary.

The runtime vocabulary is preferred when semantically equivalent, but you
may create a new stable camelCase field when the policy expresses a concept
that is not yet present in runtime state.

Operand structure:

{
  "domain": "",
  "subject": "",
  "operator": "exists",
  "expectedValue": null,
  "source": "semantic_state | decision_state | either",
  "actor": "",
  "attributes": {}
}

Do not put natural-language explanation into operand.subject.

Use a semantic field name.

======================================================================
FINDING TYPE
======================================================================

Choose findingType according to the semantic relationship expressed by
the enterprise knowledge.

Use findingType="dependency" when the policy says that one condition
triggers or requires another prerequisite, review, approval, assessment,
evaluation, or action.

Examples:
- "折扣超过10%必须评估付款周期"
  -> findingType="dependency"

- "合同签署前必须经过法务审批"
  -> findingType="dependency"

- "高风险项目必须完成安全评审"
  -> findingType="dependency"

Use findingType="gap" when the policy primarily states that required
information or a required state is absent, without a triggering dependency.

Examples:
- "项目必须有明确预算"
  -> findingType="gap"

- "合同必须包含付款周期"
  -> findingType="gap"

Do not use "gap" merely because the required operand is currently missing.
findingType describes the semantic relationship expressed by the policy,
not the current runtime evaluation result.

======================================================================
PERCENTAGES AND UNITS
======================================================================

Preserve the numeric convention already used by the supplied runtime
vocabulary when it is clear.

Otherwise preserve the human-scale numeric value from the knowledge.

Do not silently convert units unless the runtime vocabulary provides
clear evidence for the conversion.

======================================================================
SOURCE TRACEABILITY
======================================================================

Every compiled constraint MUST contain the source knowledge id in
sourceIds.

Do not cite unrelated knowledge.

======================================================================
IDENTIFIERS
======================================================================

Generate deterministic-looking ids derived from the source knowledge
id and the constraint meaning.

Do not use random UUIDs.

======================================================================
OUTPUT
======================================================================

Return JSON only.

The top-level structure MUST be:

{
  "constraints": []
}

Do not return markdown.
Do not return explanations outside JSON.
"""


class LLMConstraintCompilerBackend(
    ConstraintCompilerBackend
):
    """
    Semantic compiler backed by DecisionOS's existing LLM provider.

    Important properties:

    - no keyword-based business mapping
    - no regex business-rule fallback
    - no threshold hardcoding
    - fail closed
    - output must pass Pydantic before reaching ConstraintValidator
    """

    def __init__(
        self,
        provider=None,
    ) -> None:
        self.provider = (
            provider
            if provider is not None
            else llm_provider
        )

    async def compile_knowledge(
        self,
        *,
        knowledge: EvaluationKnowledge,
        context: EvaluationContext,
    ) -> list[EvaluationConstraint]:
        if not self.provider.enabled:
            raise RuntimeError(
                "LLM is not configured"
            )

        user_prompt = self._build_user_prompt(
            knowledge=knowledge,
            context=context,
        )

        payload = await self.provider.generate_json(
            SYSTEM_PROMPT,
            user_prompt,
            temperature=0.0,
        )

        envelope = (
            ConstraintCompilationEnvelope.model_validate(
                payload
            )
        )

        return self._enforce_source_traceability(
            constraints=envelope.constraints,
            knowledge=knowledge,
        )

    @staticmethod
    def _build_user_prompt(
        *,
        knowledge: EvaluationKnowledge,
        context: EvaluationContext,
    ) -> str:
        payload = {
            "knowledge": (
                knowledge.model_dump(
                    mode="json"
                )
            ),

            "objective": context.objective,

            "semanticSubjects": [
                subject.model_dump(
                    mode="json"
                )
                for subject
                in context.semanticSubjects
            ],

            "decisionSubjects": [
                subject.model_dump(
                    mode="json"
                )
                for subject
                in context.decisionSubjects
            ],
        }

        return (
            "Compile the following enterprise knowledge "
            "into DecisionOS EvaluationConstraint DSL.\n\n"
            + json.dumps(
                payload,
                ensure_ascii=False,
                indent=2,
            )
        )

    @staticmethod
    def _enforce_source_traceability(
        *,
        constraints: list[EvaluationConstraint],
        knowledge: EvaluationKnowledge,
    ) -> list[EvaluationConstraint]:
        """
        Structural provenance enforcement.

        This does not infer business semantics.

        A constraint compiled from one knowledge object must retain
        that knowledge object as a source.
        """

        result: list[EvaluationConstraint] = []

        for constraint in constraints:
            source_ids = list(
                constraint.sourceIds
            )

            if knowledge.id not in source_ids:
                source_ids.append(
                    knowledge.id
                )

            result.append(
                constraint.model_copy(
                    update={
                        "sourceIds": source_ids,
                    }
                )
            )

        return result