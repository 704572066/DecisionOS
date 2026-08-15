from datetime import datetime, timezone
from typing import Optional

from app.reasoning.models import Finding
from app.reasoning.finding_repository import FindingRepository


class FindingLifecycleManager:

    def __init__(
        self,
        repository: FindingRepository,
    ):
        self.repository = repository


    def evaluate(
    self,
    meeting_id: str,
    finding: Optional[Finding],
    triggered: bool,
    ) -> Optional[Finding]:

        if finding is None:
            return None


        existing = self.repository.find_by_fingerprint(
            meeting_id,
            finding.fingerprint,
        )


        now = datetime.now(timezone.utc)


        # first detection
        if existing is None:

            if triggered:
                finding.status = "open"
                finding.firstObservedAt = now
                finding.updatedAt = now

                self.repository.save(meeting_id, finding)

                return finding

            return None


        # already exists + condition remains
        if triggered:

            if existing.status == "resolved":

                # reopen
                existing.status = "open"
                existing.resolvedAt = None

            else:

                # update
                existing.status = "open"


            existing.updatedAt = now

            self.repository.update(meeting_id, existing)

            return existing


        # condition disappeared
        if existing.status == "open":

            existing.status = "resolved"
            existing.resolvedAt = now
            existing.updatedAt = now

            self.repository.update(meeting_id, existing)

            return existing


        return existing