from app.reasoning.context import (
    ConstraintOperand,
    EvaluationConstraint,
    EvaluationContext,
    EvaluationSubject,
)
from app.reasoning.models import Finding
from app.reasoning.normative_boundary_guard import (
    NormativeBoundaryGuard,
)


def context_with_discount(value: int, *, assessment: bool = False):
    subjects = [
        EvaluationSubject(
            domain="commercial",
            field="discountPercent",
            value=value,
            actor="customer",
            role="requirement",
            status="confirmed",
            sourceType="semantic_state",
            sourceId=f"event-discount-{value}",
            confidence=0.95,
        )
    ]

    if assessment:
        subjects.append(
            EvaluationSubject(
                domain="commercial",
                field="paymentTermAssessment",
                value=True,
                actor="",
                role="",
                status="confirmed",
                sourceType="semantic_state",
                sourceId="event-payment-assessment",
                confidence=0.95,
            )
        )

    return EvaluationContext(
        meetingId="meeting-test",
        contextId="context-test",
        projectId="project-test",
        semanticSubjects=subjects,
        decisionSubjects=[],
        knowledge=[],
        constraints=[],
    )


def dependency_constraint():
    return EvaluationConstraint(
        id="policy-constraint",
        domain="commercial",
        subject="discountPercent",
        subjectSource="either",
        operator=">",
        expectedValue=10,
        operand=ConstraintOperand(
            domain="commercial",
            subject="paymentTermAssessment",
            operator="exists",
            source="either",
        ),
        findingType="dependency",
        severity="high",
        evaluationMode="on_match",
        title="超过10%的折扣必须评估付款周期",
        description="当折扣超过10%时，必须评估付款周期。",
        sourceIds=["policy-test"],
    )


def general_payment_gap():
    return Finding(
        id="general-payment-gap",
        type="gap",
        status="open",
        domain="general",
        subject="付款周期",
        title="缺少付款周期信息以评估10%折扣的合规性",
        summary=(
            "公司政策要求超过10%的折扣必须评估付款周期。"
            "当前客户要求10%折扣，但未提供付款周期。"
        ),
        severity="medium",
        confidence=0.8,
        sourceIds=["policy-test"],
        fingerprint="general:payment-gap",
        attributes={
            "reasoningSource": "general",
            "generalFindingType": "missing_information",
            "suggestedAction": "向客户确认付款周期，并评估是否满足政策要求。",
        },
    )


def enterprise_dependency():
    return Finding(
        id="enterprise-dependency",
        type="dependency",
        status="open",
        domain="commercial",
        subject="discountPercent",
        title="超过10%的折扣必须评估付款周期",
        summary="当折扣超过10%时，必须评估付款周期。",
        severity="high",
        confidence=0.95,
        sourceIds=["policy-test"],
        fingerprint="enterprise:dependency",
        attributes={
            "constraintId": "policy-constraint",
            "operand": {
                "domain": "commercial",
                "subject": "paymentTermAssessment",
                "operator": "exists",
            },
        },
    )


guard = NormativeBoundaryGuard()
constraint = dependency_constraint()

# 1) Boundary case: 10 > 10 is false. General must not reinterpret it.
result_10 = guard.apply(
    context=context_with_discount(10),
    constraints=[constraint],
    enterprise_findings=[],
    general_findings=[general_payment_gap()],
)
print("10%:", result_10.diagnostics)
assert result_10.findings == []
assert result_10.diagnostics["suppressedGeneralFindings"][0]["reason"] == (
    "normative_precondition_not_satisfied"
)

# 2) 11 > 10 is true, but Enterprise already owns the issue.
result_11 = guard.apply(
    context=context_with_discount(11),
    constraints=[constraint],
    enterprise_findings=[enterprise_dependency()],
    general_findings=[general_payment_gap()],
)
print("11%:", result_11.diagnostics)
assert result_11.findings == []
assert result_11.diagnostics["suppressedGeneralFindings"][0]["reason"] == (
    "normative_issue_already_covered"
)

# 3) Primary condition applies but required operand exists: no missing warning.
result_satisfied = guard.apply(
    context=context_with_discount(15, assessment=True),
    constraints=[constraint],
    enterprise_findings=[],
    general_findings=[general_payment_gap()],
)
print("15% + assessment:", result_satisfied.diagnostics)
assert result_satisfied.findings == []
assert result_satisfied.diagnostics["suppressedGeneralFindings"][0]["reason"] == (
    "normative_requirement_already_satisfied"
)

# 4) Independent General insight that does not cite policy remains untouched.
independent = Finding(
    id="general-history",
    type="risk",
    status="open",
    domain="commercial",
    subject="discountPercent",
    title="10%高于历史成交折扣水平",
    summary="历史案例可作为谈判参考，但不是企业规则。",
    severity="medium",
    confidence=0.8,
    sourceIds=["historical-decision"],
    fingerprint="general:history",
    attributes={
        "reasoningSource": "general",
        "generalFindingType": "decision_risk",
    },
)
result_independent = guard.apply(
    context=context_with_discount(10),
    constraints=[constraint],
    enterprise_findings=[],
    general_findings=[independent],
)
assert [item.id for item in result_independent.findings] == ["general-history"]

print("PHASE 2.2.2 NORMATIVE BOUNDARY GUARD: OK")
