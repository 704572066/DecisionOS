from __future__ import annotations

from app.core.config import settings
from app.runtime.semantic_models import SemanticEventCandidate


class SemanticEventValidator:
    """Validate LLM semantic output before it reaches RuntimeStateReducer.

    This layer is intentionally deterministic. The LLM may interpret language,
    but it cannot directly mutate runtime state.
    """

    MIN_CONFIDENCE = 0.72
    MAX_EVENTS = 8

    def validate(
        self,
        events: list[SemanticEventCandidate],
        *,
        source_text: str,
    ) -> list[SemanticEventCandidate]:
        source = " ".join((source_text or "").split())
        output: list[SemanticEventCandidate] = []
        seen: set[tuple] = set()

        for event in events or []:
            if len(output) >= self.MAX_EVENTS:
                break
            min_confidence = float(
                getattr(settings, "semantic_event_min_confidence", self.MIN_CONFIDENCE)
            )
            if event.confidence < min_confidence:
                continue

            candidate = event.model_copy(deep=True)
            candidate.sourceText = " ".join(
                (candidate.sourceText or source).split()
            )
            if not candidate.sourceText:
                candidate.sourceText = source

            if not self._is_valid(candidate):
                continue

            key = (
                candidate.domain,
                candidate.kind,
                candidate.field,
                str(candidate.normalizedValue),
                candidate.relation,
                candidate.actor,
                candidate.target,
                candidate.sourceText,
            )
            if key in seen:
                continue
            seen.add(key)
            output.append(candidate)

        return output

    @staticmethod
    def _is_valid(event: SemanticEventCandidate) -> bool:
        if event.kind == "fact_change" and not event.field:
            return False

        if event.domain == "commercial":
            if event.field == "discountPercent":
                value = event.normalizedValue
                if not isinstance(value, (int, float)):
                    return False
                if not 0 <= float(value) <= 100:
                    return False
            if event.field == "paymentTermDays":
                value = event.normalizedValue
                if not isinstance(value, (int, float)):
                    return False
                if not 0 <= int(value) <= 3650:
                    return False

        return True


semantic_event_validator = SemanticEventValidator()
