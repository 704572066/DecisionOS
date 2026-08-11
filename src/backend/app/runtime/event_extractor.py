from __future__ import annotations

import re
from uuid import uuid4

from app.runtime.events import DecisionEvent
from app.runtime.models import RuntimeState


_ACCEPT_TERMS = ("同意", "接受", "可以", "确认", "没问题", "认可")
_REJECT_TERMS = ("不同意", "不接受", "不能", "拒绝", "不行")
_CONSTRAINT_TERMS = ("必须", "不得", "需要审批", "需审批", "前提是", "条件是")


class EventExtractor:
    """Small deterministic extractor for decision-changing meeting events.

    It intentionally handles only the six Sprint 3-2.2 event classes.
    """

    def extract(
        self,
        meeting_id: str,
        text: str,
        previous: RuntimeState | None,
    ) -> list[DecisionEvent]:
        source = " ".join((text or "").split())
        if not source:
            return []

        events: list[DecisionEvent] = []
        facts = (previous.decisionFacts if previous else {}) or {}

        discount = self._discount_percent(source)
        if discount is not None:
            old = facts.get("discountPercent")
            if old is None or float(old) != discount:
                events.append(
                    self._event(
                        "PriceChanged",
                        meeting_id,
                        source,
                        field="discountPercent",
                        previous=old,
                        value=discount,
                    )
                )
                # Demo policy: discounts above 10% require risk evaluation.
                # Only mark the discount risk resolved when the runtime fact
                # actually crosses back into the <=10% range.
                if old is not None and float(old) > 10 and discount <= 10:
                    events.append(
                        self._event(
                            "RiskResolved",
                            meeting_id,
                            source,
                            field="discountPercent",
                            previous=old,
                            value=discount,
                            metadata={"reason": "discount_back_within_threshold"},
                        )
                    )

        payment = self._payment_days(source)
        if payment is not None:
            old = facts.get("paymentTermDays")
            if old is None or int(old) != payment:
                events.append(
                    self._event(
                        "PaymentTermChanged",
                        meeting_id,
                        source,
                        field="paymentTermDays",
                        previous=old,
                        value=payment,
                    )
                )
                if old is not None and payment < int(old):
                    events.append(
                        self._event(
                            "RiskResolved",
                            meeting_id,
                            source,
                            field="paymentTermDays",
                            previous=old,
                            value=payment,
                            metadata={"reason": "payment_term_improved"},
                        )
                    )

        if any(term in source for term in _REJECT_TERMS):
            events.append(
                self._event(
                    "ConditionRejected",
                    meeting_id,
                    source,
                    value=source,
                )
            )
        elif any(term in source for term in _ACCEPT_TERMS):
            events.append(
                self._event(
                    "ConditionAccepted",
                    meeting_id,
                    source,
                    value=source,
                )
            )

        if any(term in source for term in _CONSTRAINT_TERMS):
            events.append(
                self._event(
                    "ConstraintAdded",
                    meeting_id,
                    source,
                    value=source,
                )
            )

        return self._dedupe(events)

    @staticmethod
    def _discount_percent(text: str) -> float | None:
        # Keep this deterministic, but accept the common negotiation forms
        # used by ASR/manual input: "折扣调整到18%", "折扣恢复到18%",
        # "价格下调至8%", and "18%的折扣".
        change_words = (
            r"(?:可以|可)?(?:调整|改|改为|变为|提高|增加|降低|降到|恢复|回到|上调|下调)?"
            r"(?:到|至|为)?"
        )
        patterns = (
            rf"(?:降价|折扣|优惠|价格(?:下降|下调)?)\s*{change_words}\s*(\d+(?:\.\d+)?)\s*%",
            r"(\d+(?:\.\d+)?)\s*%\s*(?:的)?\s*(?:折扣|降价|优惠)",
        )
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return float(match.group(1))
        return None

    @staticmethod
    def _payment_days(text: str) -> int | None:
        patterns = (
            r"(?:付款|账期|回款)(?:周期)?(?:调整|缩短|延长|改|变|可以调整|可调整|为|到|至)?\s*(?:到|至|为)?\s*(\d+)\s*天",
            r"(\d+)\s*天(?:的)?(?:付款周期|账期|回款周期)",
        )
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return int(match.group(1))
        return None

    @staticmethod
    def _event(
        event_type,
        meeting_id,
        source,
        *,
        field="",
        previous=None,
        value=None,
        metadata=None,
    ) -> DecisionEvent:
        return DecisionEvent(
            eventId="event-" + uuid4().hex[:12],
            type=event_type,
            meetingId=meeting_id,
            sourceText=source,
            field=field,
            previousValue=previous,
            value=value,
            metadata=metadata or {},
        )

    @staticmethod
    def _dedupe(events: list[DecisionEvent]) -> list[DecisionEvent]:
        seen = set()
        output = []
        for event in events:
            key = (event.type, event.field, str(event.value), event.sourceText)
            if key in seen:
                continue
            seen.add(key)
            output.append(event)
        return output


event_extractor = EventExtractor()
