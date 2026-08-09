from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field


EventType = Literal[
    "PriceChanged",
    "PaymentTermChanged",
    "ConditionAccepted",
    "ConditionRejected",
    "ConstraintAdded",
    "RiskResolved",
]


class DecisionEvent(BaseModel):
    eventId: str
    type: EventType
    meetingId: str
    sourceText: str
    field: str = ""
    previousValue: str | int | float | None = None
    value: str | int | float | None = None
    metadata: dict = Field(default_factory=dict)
    createdAt: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
