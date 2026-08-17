from __future__ import annotations

from app.reasoning.general.backend import (
    GeneralReasonerBackend,
    LLMGeneralReasonerBackend,
)
from app.reasoning.general.context import (
    GeneralReasoningContext,
)
from app.reasoning.general.finding_gate import (
    FindingGate,
    finding_gate,
)
from app.reasoning.general.models import (
    GeneralRejectedCandidate,
    GeneralReasoningDiagnostics,
    GeneralReasoningResult,
)


class GeneralReasoner:
    """
    Standalone General Reasoner.

    Phase 1.1 adds an intervention budget after deterministic Gate
    validation. A real-time monitor should surface only the most salient
    signals, even if the backend proposes more.
    """

    def __init__(
        self,
        *,
        backend: GeneralReasonerBackend | None = None,
        gate: FindingGate | None = None,
        max_findings_per_cycle: int = 5,
    ) -> None:
        self.backend = (
            backend
            if backend is not None
            else LLMGeneralReasonerBackend()
        )
        self.gate = (
            gate
            if gate is not None
            else finding_gate
        )
        self.max_findings_per_cycle = max(
            1,
            max_findings_per_cycle,
        )

    async def reason(
        self,
        context: GeneralReasoningContext,
    ) -> GeneralReasoningResult:

        diagnostics = GeneralReasoningDiagnostics(
            backend=type(self.backend).__name__
        )

        try:
            candidates = await self.backend.analyze(
                context
            )
        except Exception as exc:
            diagnostics.backendErrors.append(str(exc))
            return GeneralReasoningResult(
                meetingId=context.meetingId,
                contextId=context.contextId,
                projectId=context.projectId,
                diagnostics=diagnostics,
            )

        diagnostics.candidateCount = len(candidates)

        accepted_pairs = []
        rejected = []
        seen_fingerprints: set[str] = set()

        for candidate in candidates:
            decision = self.gate.evaluate(
                context,
                candidate,
            )

            if not decision.accepted or decision.finding is None:
                rejected.append(
                    GeneralRejectedCandidate(
                        candidate=candidate,
                        reason=decision.reason,
                        details=decision.details,
                    )
                )
                continue

            finding = decision.finding

            if finding.fingerprint in seen_fingerprints:
                rejected.append(
                    GeneralRejectedCandidate(
                        candidate=candidate,
                        reason="duplicate_novelty_key",
                        details={
                            "fingerprint": finding.fingerprint,
                        },
                    )
                )
                continue

            seen_fingerprints.add(finding.fingerprint)

            accepted_pairs.append(
                (
                    self.gate.intervention_score(candidate),
                    candidate,
                    finding,
                )
            )

        accepted_pairs.sort(
            key=lambda item: item[0],
            reverse=True,
        )

        kept = accepted_pairs[
            :self.max_findings_per_cycle
        ]
        overflow = accepted_pairs[
            self.max_findings_per_cycle:
        ]

        for score, candidate, finding in overflow:
            rejected.append(
                GeneralRejectedCandidate(
                    candidate=candidate,
                    reason="intervention_budget_exceeded",
                    details={
                        "score": score,
                        "maximumFindingsPerCycle": (
                            self.max_findings_per_cycle
                        ),
                        "fingerprint": finding.fingerprint,
                    },
                )
            )

        findings = [
            finding
            for _, _, finding in kept
        ]

        diagnostics.acceptedCount = len(findings)
        diagnostics.rejectedCount = len(rejected)
        diagnostics.budgetRejectedCount = len(overflow)
        diagnostics.metadata = {
            "maxFindingsPerCycle": self.max_findings_per_cycle,
            "acceptedScores": [
                score
                for score, _, _ in kept
            ],
        }

        return GeneralReasoningResult(
            meetingId=context.meetingId,
            contextId=context.contextId,
            projectId=context.projectId,
            candidates=candidates,
            findings=findings,
            rejected=rejected,
            diagnostics=diagnostics,
        )


general_reasoner = GeneralReasoner()
