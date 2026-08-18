from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field


DeliveryStatus = Literal["pending", "delivered", "acknowledged", "expired"]


class InterventionDelivery(BaseModel):
    id: str
    meetingId: str
    interventionId: str
    fingerprint: str = ""
    status: DeliveryStatus = "pending"
    event: dict[str, Any] = Field(default_factory=dict)
    createdAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expiresAt: datetime
    deliveredAt: datetime | None = None
    acknowledgedAt: datetime | None = None
    expiredAt: datetime | None = None
    attemptCount: int = 0
    lastError: str = ""

