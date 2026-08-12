from __future__ import annotations

import calendar
import re
from datetime import date, datetime

from app.core.config import settings
from app.runtime.semantic_models import SemanticEventCandidate


class SemanticEventValidator:
    """Deterministic governance between semantic LLM output and runtime state."""

    MIN_CONFIDENCE = 0.72
    MAX_EVENTS = 8

    def validate(
        self,
        events: list[SemanticEventCandidate],
        *,
        source_text: str,
        meeting_date: datetime | date | None = None,
    ) -> list[SemanticEventCandidate]:
        source = " ".join((source_text or "").split())
        anchor = self._as_date(meeting_date)
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
            ) or source

            self._normalize_actor(candidate)
            self._normalize_approval_domain(candidate)
            self._normalize_date(candidate, anchor)

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
    def _as_date(value: datetime | date | None) -> date | None:
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, date):
            return value
        return None

    @staticmethod
    def _normalize_actor(event: SemanticEventCandidate) -> None:
        raw = (event.actor or "").strip()
        lowered = raw.lower()
        if not raw or lowered in {"unknown", "未知", "不明"}:
            event.actor = "unknown"
            return
        if lowered in {"customer", "客户", "客户方", "对方"}:
            event.actor = "customer"
            return
        if lowered in {"us", "we", "我方", "我们", "项目组", "本方"}:
            event.actor = "us"
            return
        if lowered in {"third_party", "第三方"}:
            event.actor = "third_party"
            return
        event.metadata = dict(event.metadata or {})
        event.metadata.setdefault("actorText", raw)
        event.actor = "third_party"

    @staticmethod
    def _normalize_approval_domain(event: SemanticEventCandidate) -> None:
        if event.domain != "contract" or event.kind != "dependency":
            return
        field = (event.field or "").lower()
        relation = (event.relation or "").lower()
        target = (event.target or "").lower()
        value = str(event.normalizedValue if event.normalizedValue is not None else event.value).lower()
        approval_semantics = (
            "approval" in field
            or "approve" in field
            or "review" in field
            or "signing" in field
            or relation in {"requires", "depends_on", "conditional_on"}
            and any(token in (field + target + value) for token in (
                "法务", "审批", "批准", "确认", "授权", "review", "approval", "legal"
            ))
        )
        if approval_semantics:
            event.metadata = dict(event.metadata or {})
            event.metadata.setdefault("originalDomain", "contract")
            event.domain = "approval"
            if event.field in {"signing", "contractSigning", ""}:
                event.field = "contractApproval"

    @classmethod
    def _normalize_date(
        cls,
        event: SemanticEventCandidate,
        meeting_date: date | None,
    ) -> None:
        if meeting_date is None or event.domain != "delivery":
            return
        source = event.sourceText or ""

        # Chinese month/day without year: choose the next non-past occurrence.
        match = re.search(r"(?<!\d)(\d{1,2})\s*月\s*(\d{1,2})\s*日?", source)
        if match and not re.search(r"\d{4}\s*年", source):
            month, day = int(match.group(1)), int(match.group(2))
            try:
                candidate = date(meeting_date.year, month, day)
                if candidate < meeting_date:
                    candidate = date(meeting_date.year + 1, month, day)
                event.normalizedValue = candidate.isoformat()
                return
            except ValueError:
                return

        if "月底" in source:
            last_day = calendar.monthrange(meeting_date.year, meeting_date.month)[1]
            event.normalizedValue = date(
                meeting_date.year,
                meeting_date.month,
                last_day,
            ).isoformat()
            return

        # Guard against an LLM assigning a past year to a source that omits a year.
        value = event.normalizedValue
        if isinstance(value, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
            try:
                parsed = date.fromisoformat(value)
            except ValueError:
                return
            if parsed < meeting_date and not cls._explicit_past_reference(source):
                try:
                    adjusted = date(meeting_date.year, parsed.month, parsed.day)
                    if adjusted < meeting_date:
                        adjusted = date(meeting_date.year + 1, parsed.month, parsed.day)
                    event.normalizedValue = adjusted.isoformat()
                except ValueError:
                    pass

    @staticmethod
    def _explicit_past_reference(source: str) -> bool:
        return any(token in source for token in (
            "去年", "上个月", "上周", "之前", "此前", "过去", "曾经", "原计划"
        ))

    @staticmethod
    def _is_valid(event: SemanticEventCandidate) -> bool:
        if event.kind == "fact_change" and not event.field:
            return False

        if event.actor not in {"customer", "us", "third_party", "unknown"}:
            return False

        if event.domain == "commercial":
            if event.field == "discountPercent":
                value = event.normalizedValue
                if not isinstance(value, (int, float)) or not 0 <= float(value) <= 100:
                    return False
            if event.field == "paymentTermDays":
                value = event.normalizedValue
                if not isinstance(value, (int, float)) or not 0 <= int(value) <= 3650:
                    return False

        return True


semantic_event_validator = SemanticEventValidator()
