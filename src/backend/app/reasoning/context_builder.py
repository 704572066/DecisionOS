from __future__ import annotations

from typing import Any

from app.reasoning.context import (
    EvaluationContext,
    EvaluationKnowledge,
    EvaluationSubject,
)
from app.runtime.models import RuntimeState


class EvaluationContextBuilder:
    """
    Convert RuntimeState into the normalized input consumed by
    the future Generic Evaluator.

    Responsibilities:

        RuntimeState
            ↓
        EvaluationContext

    This builder DOES:
    - flatten semanticState into semanticSubjects
    - flatten decisionState into decisionSubjects
    - normalize rerankedEvidence into EvaluationKnowledge
    - preserve objective / meeting / project / context metadata

    This builder DOES NOT:
    - evaluate risk
    - compare thresholds
    - interpret policy text
    - create EvaluationConstraint from natural language
    - decide severity
    - generate Finding
    """

    #
    # Keys describing a decision object itself rather than an independent
    # decision subject.
    #
    # Example:
    #
    # {
    #   "goLiveDate": "2026-10-01",
    #   "relation": "<=",
    #   "role": "commitment",
    #   "status": "confirmed"
    # }
    #
    # Only goLiveDate is the subject.
    #
    DESCRIPTOR_KEYS = {
        "domain",
        "field",
        "value",
        "relation",
        "role",
        "actor",
        "status",
        "target",
        "sourceText",
        "sourceId",
        "eventId",
        "confidence",
        "required",
    }

    def build(
        self,
        state: RuntimeState,
    ) -> EvaluationContext:
        decision_facts = dict(
            state.decisionFacts or {}
        )

        semantic_state = dict(
            decision_facts.get("semanticState")
            or {}
        )

        decision_state = dict(
            state.decisionState or {}
        )

        return EvaluationContext(
            meetingId=state.meetingId,
            contextId=state.contextId,
            projectId=state.projectId,
            objective=state.objective,

            semanticSubjects=self._semantic_subjects(
                semantic_state
            ),

            decisionSubjects=self._decision_subjects(
                decision_state
            ),

            knowledge=self._knowledge(
                state.rerankedEvidence
            ),

            #
            # IMPORTANT:
            #
            # Do NOT copy RuntimeState.constraints here.
            #
            # RuntimeState.constraints are not guaranteed to follow the
            # machine-executable EvaluationConstraint contract.
            #
            # Natural-language policy -> EvaluationConstraint belongs to
            # a later policy/constraint compiler.
            #
            constraints=[],

            metadata={
                "retrievalMode": state.retrievalMode,

                "topics": list(
                    state.topics or []
                ),

                "runtimeFacts": list(
                    state.facts or []
                ),

                "runtimeConstraints": list(
                    state.constraints or []
                ),

                "resolvedRiskKeys": list(
                    state.resolvedRiskKeys or []
                ),

                "runtimeUpdatedAt": (
                    state.updatedAt.isoformat()
                    if state.updatedAt
                    else None
                ),
            },
        )

    @classmethod
    def _semantic_subjects(
        cls,
        semantic_state: dict[str, Any],
    ) -> list[EvaluationSubject]:
        """
        semanticState already represents current participant positions.

        Preserve:
        - domain
        - field
        - value
        - actor
        - role
        - status
        - relation
        - sourceText

        Do not reinterpret their meaning.
        """

        output: list[EvaluationSubject] = []

        for domain, raw_items in (
            semantic_state or {}
        ).items():
            if not isinstance(
                raw_items,
                list,
            ):
                continue

            for item in raw_items:
                if not isinstance(
                    item,
                    dict,
                ):
                    continue

                field = str(
                    item.get("field")
                    or ""
                ).strip()

                if not field:
                    continue

                confidence = cls._confidence(
                    item.get("confidence")
                )

                output.append(
                    EvaluationSubject(
                        domain=str(
                            item.get("domain")
                            or domain
                            or ""
                        ),

                        field=field,

                        value=item.get("value"),

                        actor=str(
                            item.get("actor")
                            or "unknown"
                        ),

                        role=str(
                            item.get("role")
                            or "unknown"
                        ),

                        status=str(
                            item.get("status")
                            or ""
                        ),

                        relation=str(
                            item.get("relation")
                            or ""
                        ),

                        sourceText=str(
                            item.get("sourceText")
                            or ""
                        ),

                        sourceType=(
                            "semantic_state"
                        ),

                        sourceId=str(
                            item.get("eventId")
                            or item.get("sourceId")
                            or ""
                        ),

                        confidence=confidence,

                        metadata={
                            "kind": (
                                item.get("kind")
                                or ""
                            ),
                            "target": (
                                item.get("target")
                                or ""
                            ),
                        },
                    )
                )

        return output

    @classmethod
    def _decision_subjects(
        cls,
        decision_state: dict[str, Any],
    ) -> list[EvaluationSubject]:
        """
        Convert the resolved decisionState into generic subjects.

        This implementation deliberately does not know about:
        - discountPercent
        - paymentTermDays
        - legalApproval
        - scopeInclusion
        - goLiveDate

        It derives subjects from the shape of decisionState instead.
        """

        output: list[EvaluationSubject] = []

        for domain, payload in (
            decision_state or {}
        ).items():

            if not isinstance(
                payload,
                dict,
            ):
                continue

            #
            # Shape A:
            #
            # {
            #   "field": "scopeInclusion",
            #   "value": "...",
            #   "relation": "removes",
            #   ...
            # }
            #
            explicit_field = str(
                payload.get("field")
                or ""
            ).strip()

            if explicit_field:
                output.append(
                    cls._decision_subject_from_descriptor(
                        domain=domain,
                        field=explicit_field,
                        descriptor=payload,
                    )
                )
                continue

            #
            # Shape B:
            #
            # commercial:
            # {
            #   "discountPercent": 15,
            #   "paymentTermDays": 90
            # }
            #
            # Shape C:
            #
            # approval:
            # {
            #   "legalApproval": {
            #       "required": true,
            #       "value": "...",
            #       ...
            #   }
            # }
            #
            # Shape D:
            #
            # delivery:
            # {
            #   "goLiveDate": "...",
            #   "relation": "...",
            #   "status": "..."
            # }
            #

            shared_descriptor = {
                key: value
                for key, value in payload.items()
                if key in cls.DESCRIPTOR_KEYS
            }

            for field, value in payload.items():
                if field in cls.DESCRIPTOR_KEYS:
                    continue

                if isinstance(
                    value,
                    dict,
                ):
                    descriptor = dict(value)

                    output.append(
                        cls._decision_subject_from_descriptor(
                            domain=domain,
                            field=field,
                            descriptor=descriptor,
                        )
                    )

                    continue

                descriptor = {
                    **shared_descriptor,
                    "value": value,
                }

                output.append(
                    cls._decision_subject_from_descriptor(
                        domain=domain,
                        field=field,
                        descriptor=descriptor,
                    )
                )

        return output

    @classmethod
    def _decision_subject_from_descriptor(
        cls,
        *,
        domain: str,
        field: str,
        descriptor: dict[str, Any],
    ) -> EvaluationSubject:
        """
        Normalize one decisionState entry without interpreting its
        business meaning.
        """

        value = descriptor.get("value")

        #
        # Some dependency/approval objects expose:
        #
        # required: true
        #
        # and may not contain a separate value.
        #
        if (
            value is None
            and "required" in descriptor
        ):
            value = descriptor.get(
                "required"
            )

        metadata = {
            key: val
            for key, val in descriptor.items()
            if key not in {
                "field",
                "value",
                "relation",
                "role",
                "actor",
                "status",
                "sourceText",
                "sourceId",
                "eventId",
                "confidence",
            }
        }

        return EvaluationSubject(
            domain=str(
                domain or ""
            ),

            field=str(
                field or ""
            ),

            value=value,

            actor=str(
                descriptor.get("actor")
                or ""
            ),

            role=str(
                descriptor.get("role")
                or ""
            ),

            status=str(
                descriptor.get("status")
                or ""
            ),

            relation=str(
                descriptor.get("relation")
                or ""
            ),

            sourceText=str(
                descriptor.get("sourceText")
                or ""
            ),

            sourceType="decision_state",

            sourceId=str(
                descriptor.get("sourceId")
                or descriptor.get("eventId")
                or ""
            ),

            confidence=cls._confidence(
                descriptor.get("confidence")
            ),

            metadata=metadata,
        )

    @classmethod
    def _knowledge(
        cls,
        evidence: list[dict],
    ) -> list[EvaluationKnowledge]:
        """
        Normalize current reranked enterprise evidence.

        Existing repository conventions:

        id:
            objectId or itemId

        source type:
            sourceType or objectType

        score:
            rerankScore or score
        """

        output: list[EvaluationKnowledge] = []
        seen: set[str] = set()

        for item in evidence or []:
            if not isinstance(
                item,
                dict,
            ):
                continue

            object_id = str(
                item.get("objectId")
                or item.get("itemId")
                or ""
            ).strip()

            if not object_id:
                continue

            if object_id in seen:
                continue

            seen.add(
                object_id
            )

            source_type = str(
                item.get("sourceType")
                or item.get("objectType")
                or "knowledge"
            )

            score = cls._score(
                item.get("rerankScore")
                if item.get("rerankScore")
                is not None
                else item.get("score")
            )

            #
            # Preserve additional retrieval/rerank information without
            # coupling EvaluationKnowledge to the retrieval implementation.
            #
            attributes = {
                key: value
                for key, value in item.items()
                if key not in {
                    "objectId",
                    "itemId",
                    "sourceType",
                    "objectType",
                    "title",
                    "summary",
                    "content",
                    "rerankScore",
                    "score",
                }
            }

            output.append(
                EvaluationKnowledge(
                    id=object_id,

                    sourceType=source_type,

                    title=str(
                        item.get("title")
                        or ""
                    ),

                    summary=str(
                        item.get("summary")
                        or ""
                    ),

                    content=str(
                        item.get("content")
                        or item.get("summary")
                        or ""
                    ),

                    score=score,

                    attributes=attributes,
                )
            )

        output.sort(
            key=lambda item: item.score,
            reverse=True,
        )

        return output

    @staticmethod
    def _confidence(
        value: Any,
    ) -> float:
        if value is None:
            return 1.0

        try:
            number = float(value)
        except (
            TypeError,
            ValueError,
        ):
            return 1.0

        return max(
            0.0,
            min(
                1.0,
                number,
            ),
        )

    @staticmethod
    def _score(
        value: Any,
    ) -> float:
        if value is None:
            return 0.0

        try:
            number = float(value)
        except (
            TypeError,
            ValueError,
        ):
            return 0.0

        return max(
            0.0,
            min(
                1.0,
                number,
            ),
        )


evaluation_context_builder = (
    EvaluationContextBuilder()
)