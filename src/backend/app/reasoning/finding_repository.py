from typing import Dict, Optional, List, Tuple

from app.reasoning.models import Finding


class FindingRepository:

    def __init__(self):
        self._findings: Dict[Tuple[str, str], Finding] = {}

    def _key(
        self,
        meeting_id: str,
        fingerprint: str,
    ) -> Tuple[str, str]:
        return meeting_id, fingerprint

    def save(
        self,
        meeting_id: str,
        finding: Finding,
    ) -> Finding:
        self._findings[
            self._key(meeting_id, finding.fingerprint)
        ] = finding
        return finding

    def find_by_fingerprint(
        self,
        meeting_id: str,
        fingerprint: str,
    ) -> Optional[Finding]:
        return self._findings.get(
            self._key(meeting_id, fingerprint)
        )

    def update(
        self,
        meeting_id: str,
        finding: Finding,
    ) -> Finding:
        self._findings[
            self._key(meeting_id, finding.fingerprint)
        ] = finding
        return finding

    def list(
        self,
        meeting_id: Optional[str] = None,
    ) -> List[Finding]:

        if meeting_id is None:
            return list(self._findings.values())

        return [
            finding
            for (stored_meeting_id, _), finding
            in self._findings.items()
            if stored_meeting_id == meeting_id
        ]