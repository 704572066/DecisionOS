from app.reasoning.models import Finding
from app.reasoning.shared_finding_merger import SharedFindingMerger


def finding(fid, title, subject, source, fingerprint, reasoning_source=None):
    attrs = {}
    if reasoning_source:
        attrs["reasoningSource"] = reasoning_source
    return Finding(
        id=fid,
        type="risk",
        status="open",
        domain="commercial",
        subject=subject,
        title=title,
        sourceIds=[source],
        fingerprint=fingerprint,
        attributes=attrs,
    )


enterprise = [
    finding(
        "policy-1",
        "超过10%的折扣必须评估付款周期",
        "discountPercent",
        "policy-source",
        "policy:fingerprint",
        "policy",
    )
]

general = [
    finding(
        "general-duplicate",
        "折扣风险",
        "discountPercent",
        "runtime-source",
        "general:discount",
        "general",
    ),
    finding(
        "general-new",
        "行业增长预测需要验证",
        "industryGrowth",
        "runtime-context:test",
        "general:growth",
        "general",
    ),
]

result = SharedFindingMerger().merge(
    meeting_id="meeting-test",
    context_id="context-test",
    enterprise_findings=enterprise,
    general_findings=general,
)

print("findings:", [item.id for item in result.findings])
print("diagnostics:", result.diagnostics)

assert [item.id for item in result.findings] == [
    "policy-1",
    "general-new",
]
assert result.diagnostics["suppressedGeneralFindingCount"] == 1
print("SHARED FINDING MERGER: OK")
