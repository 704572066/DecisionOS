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
    Phase-1 standalone General Reasoner.

    It is intentionally NOT wired into ReasoningService yet.

    Pipeline:
        GeneralReasoningContext
            -> backend candidate proposal
            -> deterministic FindingGate
            -> standard Finding[]
    """

    def __init__(
        self,
        *,
        backend: GeneralReasonerBackend | None = None,
        gate: FindingGate | None = None,
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
            diagnostics.backendErrors.append(
                str(exc)
            )
            return GeneralReasoningResult(
                meetingId=context.meetingId,
                contextId=context.contextId,
                projectId=context.projectId,
                diagnostics=diagnostics,
            )

        diagnostics.candidateCount = len(
            candidates
        )

        findings = []
        rejected = []
        seen_fingerprints: set[str] = set()

        for candidate in candidates:
            decision = self.gate.evaluate(
                context,
                candidate,
            )

            if (
                not decision.accepted
                or decision.finding is None
            ):
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
                            "fingerprint": (
                                finding.fingerprint
                            )
                        },
                    )
                )
                continue

            seen_fingerprints.add(
                finding.fingerprint
            )
            findings.append(finding)

        diagnostics.acceptedCount = len(
            findings
        )
        diagnostics.rejectedCount = len(
            rejected
        )

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
