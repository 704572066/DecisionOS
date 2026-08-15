from typing import Dict, Optional, List

from app.reasoning.models import Finding


class FindingRepository:

    def __init__(self):
        self._findings: Dict[str, Finding] = {}

    def save(self, finding: Finding) -> Finding:
        self._findings[finding.fingerprint] = finding
        return finding

    def find_by_fingerprint(
        self,
        fingerprint: str
    ) -> Optional[Finding]:
        return self._findings.get(fingerprint)

    def update(
        self,
        finding: Finding
    ) -> Finding:
        self._findings[finding.fingerprint] = finding
        return finding

    def list(self) -> List[Finding]:
        return list(self._findings.values())