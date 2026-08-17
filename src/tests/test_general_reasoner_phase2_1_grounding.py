from app.reasoning.models import Finding
from app.reasoning.shared_finding_merger import SharedFindingMerger


enterprise = Finding(
    id="policy-dependency",
    type="dependency",
    status="open",
    domain="commercial",
    subject="discountPercent",
    title="超过10%的折扣必须评估付款周期",
    summary="超过10%时必须评估付款周期。",
    severity="high",
    confidence=0.95,
    fingerprint="policy:discount:payment",
    attributes={
        "constraintId": "policy-1",
        "operand": {
            "domain": "commercial",
            "subject": "paymentTermAssessment",
            "operator": "exists",
            "expectedValue": None,
            "source": "either",
        },
    },
)

duplicate_general = Finding(
    id="general-payment-gap",
    type="gap",
    status="open",
    domain="commercial",
    subject="paymentTermAssessment",
    title="缺少付款周期评估信息",
    summary="当前缺少付款周期评估。",
    severity="high",
    confidence=0.9,
    fingerprint="general:payment-gap",
    attributes={
        "reasoningSource": "general",
        "generalFindingType": "missing_information",
        "noveltyKey": "missing-payment-term-assessment",
    },
)

independent_general = Finding(
    id="general-independent",
    type="risk",
    status="open",
    domain="commercial",
    subject="externalClaim",
    title="一个独立的通用风险",
    summary="不被企业规则覆盖。",
    severity="medium",
    confidence=0.8,
    fingerprint="general:independent",
    attributes={
        "reasoningSource": "general",
        "generalFindingType": "claim",
        "noveltyKey": "independent",
    },
)

result = SharedFindingMerger().merge(
    meeting_id="meeting-test",
    context_id="context-test",
    enterprise_findings=[enterprise],
    general_findings=[
        duplicate_general,
        independent_general,
    ],
)

print("findings:", [x.id for x in result.findings])
print("diagnostics:", result.diagnostics)

assert [x.id for x in result.findings] == [
    "policy-dependency",
    "general-independent",
]

suppressed = result.diagnostics[
    "suppressedGeneralFindings"
]

assert len(suppressed) == 1
assert suppressed[0]["findingId"] == "general-payment-gap"
assert (
    suppressed[0]["reason"]
    == "enterprise_dependency_operand_already_covered"
)

print("PHASE 2.1 POLICY COVERAGE DEDUP: OK")
