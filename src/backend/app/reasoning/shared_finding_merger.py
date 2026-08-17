from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.reasoning.models import Finding, FindingSet


@dataclass
class SharedFindingMergeDiagnostics:
    enterpriseFindingCount: int = 0
    generalFindingCount: int = 0
    mergedFindingCount: int = 0
    suppressedGeneralFindingCount: int = 0
    suppressedGeneralFindings: list[dict[str, Any]] = field(
        default_factory=list
    )

    def as_dict(self) -> dict[str, Any]:
        return {
            "enterpriseFindingCount": self.enterpriseFindingCount,
            "generalFindingCount": self.generalFindingCount,
            "mergedFindingCount": self.mergedFindingCount,
            "suppressedGeneralFindingCount": (
                self.suppressedGeneralFindingCount
            ),
            "suppressedGeneralFindings": list(
                self.suppressedGeneralFindings
            ),
        }


class SharedFindingMerger:
    """
    Merge precise enterprise-policy findings with General Reasoner findings.

    Enterprise findings always have priority. The merger is deliberately
    conservative: it suppresses only deterministic duplicates rather than
    trying to perform another semantic reasoning pass.

    General Reasoner already receives activePolicyFindings in its context and
    should avoid restating them. This merger is the final structural safety
    net for exact/near-exact duplicates.
    """

    def merge(
        self,
        *,
        meeting_id: str,
        context_id: str,
        enterprise_findings: list[Finding],
        general_findings: list[Finding],
    ) -> FindingSet:
        diagnostics = SharedFindingMergeDiagnostics(
            enterpriseFindingCount=len(enterprise_findings),
            generalFindingCount=len(general_findings),
        )

        merged = list(enterprise_findings)

        enterprise_fingerprints = {
            item.fingerprint
            for item in enterprise_findings
            if item.fingerprint
        }
        enterprise_titles = {
            self._normalize(item.title)
            for item in enterprise_findings
            if item.title
        }
        enterprise_subjects = {
            (
                self._normalize(item.domain),
                self._normalize(item.subject),
            )
            for item in enterprise_findings
            if item.subject
        }

        # Subjects that are already represented by an enterprise
        # dependency operand are part of the same underlying issue.
        #
        # Example:
        #   Enterprise:
        #       discountPercent > 10 requires paymentTermAssessment
        #
        #   General:
        #       missing_information / paymentTermAssessment
        #
        # The General finding is a restatement of the enterprise
        # dependency and must be suppressed.
        enterprise_operand_subjects = (
            self._enterprise_operand_subjects(
                enterprise_findings
            )
        )

        seen_general_fingerprints: set[str] = set()

        for finding in general_findings:
            reason = ""

            if (
                finding.fingerprint
                and finding.fingerprint in enterprise_fingerprints
            ):
                reason = "duplicate_enterprise_fingerprint"

            elif (
                finding.title
                and self._normalize(finding.title) in enterprise_titles
            ):
                reason = "duplicate_enterprise_title"

            elif finding.subject:
                key = (
                    self._normalize(finding.domain),
                    self._normalize(finding.subject),
                )
                if key in enterprise_subjects:
                    reason = "enterprise_subject_already_covered"

                elif self._is_general_missing_information(finding):
                    # Phase 2.2: LLM domains are advisory. Operand coverage is
                    # determined primarily by canonical subject identity so a
                    # `general/paymentTermAssessment` restatement is still
                    # suppressed by a `commercial` enterprise dependency.
                    normalized_subject = self._normalize(finding.subject)
                    if any(
                        operand_subject == normalized_subject
                        for _, operand_subject in enterprise_operand_subjects
                    ):
                        reason = (
                            "enterprise_dependency_operand_already_covered"
                        )

            if (
                not reason
                and finding.fingerprint
                and finding.fingerprint in seen_general_fingerprints
            ):
                reason = "duplicate_general_fingerprint"

            if reason:
                diagnostics.suppressedGeneralFindingCount += 1
                diagnostics.suppressedGeneralFindings.append(
                    {
                        "findingId": finding.id,
                        "fingerprint": finding.fingerprint,
                        "reason": reason,
                    }
                )
                continue

            if finding.fingerprint:
                seen_general_fingerprints.add(
                    finding.fingerprint
                )

            merged.append(finding)

        diagnostics.mergedFindingCount = len(merged)

        return FindingSet(
            meetingId=meeting_id,
            contextId=context_id,
            findings=merged,
            diagnostics=diagnostics.as_dict(),
        )

    @classmethod
    def _enterprise_operand_subjects(
        cls,
        findings: list[Finding],
    ) -> set[tuple[str, str]]:
        output: set[tuple[str, str]] = set()

        for finding in findings:
            attributes = dict(
                finding.attributes or {}
            )

            operand = attributes.get(
                "operand"
            )

            if not isinstance(
                operand,
                dict,
            ):
                continue

            subject = cls._normalize(
                operand.get(
                    "subject",
                    ""
                )
            )

            if not subject:
                continue

            operand_domain = cls._normalize(
                operand.get(
                    "domain",
                    ""
                )
                or finding.domain
            )

            output.add(
                (
                    operand_domain,
                    subject,
                )
            )

        return output

    @staticmethod
    def _is_general_missing_information(
        finding: Finding,
    ) -> bool:
        attributes = dict(
            finding.attributes or {}
        )

        return (
            attributes.get(
                "reasoningSource"
            )
            == "general"
            and attributes.get(
                "generalFindingType"
            )
            == "missing_information"
        )

    @staticmethod
    def _normalize(value: str) -> str:
        return "".join(
            str(value or "").lower().split()
        )


shared_finding_merger = SharedFindingMerger()
