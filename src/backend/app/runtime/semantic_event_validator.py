from __future__ import annotations

import calendar
import re
from datetime import date, datetime

from app.core.config import settings
from app.runtime.semantic_models import SemanticEventCandidate

class SemanticEventValidator:
    """
    Deterministic governance between semantic LLM output and runtime state.

    Responsibilities:
    - confidence filtering
    - semantic normalization
    - actor normalization
    - role resolution
    - domain correction
    - duplicate filtering
    """

    MIN_CONFIDENCE = 0.72
    MAX_EVENTS = 8


    def validate(
        self,
        events: list[SemanticEventCandidate],
        *,
        source_text: str,
        meeting_date: datetime | date | None = None,
    ) -> list[SemanticEventCandidate]:

        source = " ".join(
            (source_text or "").split()
        )

        anchor = self._as_date(
            meeting_date
        )

        output = []
        seen = set()


        min_confidence = float(
            getattr(
                settings,
                "semantic_event_min_confidence",
                self.MIN_CONFIDENCE,
            )
        )


        for event in events or []:

            if len(output) >= self.MAX_EVENTS:
                break


            if event.confidence < min_confidence:
                continue


            candidate = event.model_copy(
                deep=True
            )


            candidate.sourceText = (
                " ".join(
                    (
                        candidate.sourceText
                        or source
                    ).split()
                )
                or source
            )


            self._normalize_actor(
                candidate
            )

            self._normalize_role(
                candidate
            )

            self._normalize_approval_domain(
                candidate
            )

            self._normalize_date(
                candidate,
                anchor,
            )


            if not self._is_valid(candidate):
                continue


            key = (
                candidate.domain,
                candidate.kind,
                candidate.field,
                str(candidate.normalizedValue),
                candidate.relation,
                candidate.role,
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
    def _as_date(
        value
    ) -> date | None:

        if isinstance(value, datetime):
            return value.date()

        if isinstance(value, date):
            return value

        return None



    @staticmethod
    def _normalize_role(
        event: SemanticEventCandidate,
    ) -> None:


        allowed = {
            "requirement",
            "proposal",
            "commitment",
            "acceptance",
            "assessment",
            "dependency",
            "liability",
            "unknown",
        }


        role = (
            event.role
            or "unknown"
        ).strip().lower()


        # 已经明确角色
        # unknown 不可信，需要重新推断
        if (
            role in allowed
            and role != "unknown"
        ):
            return


        resolved = (
            semantic_role_resolver.resolve(
                event.model_dump()
            )
        )


        if resolved:
            event.role = resolved
        else:
            event.role = "unknown"



    @staticmethod
    def _normalize_actor(
        event: SemanticEventCandidate,
    ) -> None:

        raw = (
            event.actor
            or ""
        ).strip()


        lowered = raw.lower()


        if (
            not raw
            or lowered in {
                "unknown",
                "未知",
                "不明",
            }
        ):
            event.actor = "unknown"
            return


        if lowered in {
            "customer",
            "客户",
            "客户方",
            "对方",
        }:
            event.actor = "customer"
            return


        if lowered in {
            "us",
            "we",
            "我方",
            "我们",
            "项目组",
            "本方",
        }:
            event.actor = "us"
            return


        if lowered in {
            "third_party",
            "第三方",
        }:
            event.actor = "third_party"
            return


        event.metadata = dict(
            event.metadata or {}
        )

        event.metadata.setdefault(
            "actorText",
            raw,
        )

        event.actor = "third_party"



    @staticmethod
    def _normalize_approval_domain(
        event: SemanticEventCandidate,
    ) -> None:

        if (
            event.domain != "contract"
            or event.kind != "dependency"
        ):
            return


        field = (
            event.field
            or ""
        ).lower()

        relation = (
            event.relation
            or ""
        ).lower()

        target = (
            event.target
            or ""
        ).lower()

        value = str(
            event.normalizedValue
            if event.normalizedValue is not None
            else event.value
        ).lower()


        approval = (
            "approval" in field
            or "approve" in field
            or "review" in field
            or "signing" in field
            or (
                relation
                in {
                    "requires",
                    "depends_on",
                    "conditional_on",
                }
                and any(
                    token in (
                        field
                        + target
                        + value
                    )
                    for token in (
                        "法务",
                        "审批",
                        "批准",
                        "确认",
                        "授权",
                        "legal",
                        "approval",
                    )
                )
            )
        )


        if approval:

            event.metadata = dict(
                event.metadata or {}
            )

            event.metadata.setdefault(
                "originalDomain",
                "contract",
            )

            event.domain = "approval"


            if event.field in {
                "signing",
                "contractSigning",
                "",
            }:
                event.field = (
                    "contractApproval"
                )



    @classmethod
    def _normalize_date(
        cls,
        event,
        meeting_date,
    ):

        if (
            meeting_date is None
            or event.domain != "delivery"
        ):
            return


        source = (
            event.sourceText
            or ""
        )


        match = re.search(
            r"(?<!\d)(\d{1,2})\s*月\s*(\d{1,2})\s*日?",
            source,
        )


        if (
            match
            and not re.search(
                r"\d{4}\s*年",
                source,
            )
        ):

            month = int(
                match.group(1)
            )

            day = int(
                match.group(2)
            )


            try:

                candidate = date(
                    meeting_date.year,
                    month,
                    day,
                )


                if candidate < meeting_date:
                    candidate = date(
                        meeting_date.year + 1,
                        month,
                        day,
                    )


                event.normalizedValue = (
                    candidate.isoformat()
                )

            except ValueError:
                pass



    @staticmethod
    def _is_valid(
        event,
    ) -> bool:


        if (
            event.kind == "fact_change"
            and not event.field
        ):
            return False


        if event.actor not in {
            "customer",
            "us",
            "third_party",
            "unknown",
        }:
            return False


        if event.domain == "commercial":


            if event.field == "discountPercent":

                value = event.normalizedValue

                if not isinstance(
                    value,
                    (int, float),
                ):
                    return False


                if not (
                    0 <= float(value) <= 100
                ):
                    return False



            if event.field == "paymentTermDays":

                value = event.normalizedValue

                if not isinstance(
                    value,
                    (int, float),
                ):
                    return False


                if not (
                    0 <= int(value) <= 3650
                ):
                    return False


        return True



semantic_event_validator = SemanticEventValidator()