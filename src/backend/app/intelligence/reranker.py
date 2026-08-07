from __future__ import annotations

from dataclasses import dataclass
from app.context.models import BusinessContext


@dataclass(slots=True)
class RankedEvidence:
    item: dict
    retrieval_score: float
    context_score: float
    final_score: float
    reasons: list[str]


_OBJECT_BOOST = {
    "decision": 0.10,
    "evidence": 0.08,
    "document": 0.03,
    "meeting": 0.02,
}

_POLICY_TERMS = ("规则", "政策", "制度", "不得", "必须", "审批", "毛利率", "利润率")
_RISK_TERMS = ("风险", "逾期", "坏账", "违约", "担保", "不得", "必须")
_PRICE_TERMS = ("价格", "折扣", "降价", "报价", "毛利", "利润")
_PAYMENT_TERMS = ("付款", "账期", "回款", "周期", "预付", "分阶段")
_DELIVERY_TERMS = ("交付", "验收", "上线", "延期", "工期")


def rerank_context(
    context: BusinessContext,
    retrieval_results: list[dict],
    *,
    top_k: int = 5,
) -> list[RankedEvidence]:
    ranked: list[RankedEvidence] = []
    objective = context.currentObjective or ""
    topics = set(context.topics)
    facts = [fact.normalizedValue or fact.text for fact in context.facts]

    for item in retrieval_results:
        text = f"{item.get('title','')}\n{item.get('summary','')}"
        retrieval_score = float(item.get("score") or 0.0)
        bonus = _OBJECT_BOOST.get(item.get("objectType"), 0.0)
        reasons: list[str] = []

        for topic in topics:
            if topic and topic in text:
                bonus += 0.035
                reasons.append(f"匹配当前议题:{topic}")

        for fact in facts:
            if fact and fact in text:
                bonus += 0.06
                reasons.append(f"匹配关键事实:{fact}")

        if objective:
            if any(term in objective for term in ("利润", "毛利")) and any(
                term in text for term in ("利润", "毛利", "折扣", "价格")
            ):
                bonus += 0.11
                reasons.append("匹配利润目标")
            if "签约" in objective and any(
                term in text for term in ("合同", "成交", "签约", "付款", "折扣")
            ):
                bonus += 0.04
                reasons.append("匹配签约目标")

        if "付款" in topics and any(term in text for term in _PAYMENT_TERMS):
            bonus += 0.07
            reasons.append("付款议题增强")
        if "价格" in topics and any(term in text for term in _PRICE_TERMS):
            bonus += 0.07
            reasons.append("价格议题增强")
        if "交付" in topics and any(term in text for term in _DELIVERY_TERMS):
            bonus += 0.07
            reasons.append("交付议题增强")

        if any(term in text for term in _POLICY_TERMS):
            bonus += 0.045
            reasons.append("政策/规则证据")
        if any(term in text for term in _RISK_TERMS):
            bonus += 0.035
            reasons.append("风险证据")

        final_score = min(1.0, retrieval_score * 0.78 + bonus)
        ranked.append(
            RankedEvidence(
                item=item,
                retrieval_score=retrieval_score,
                context_score=min(1.0, bonus),
                final_score=final_score,
                reasons=reasons,
            )
        )

    ranked.sort(
        key=lambda row: (
            row.final_score,
            row.retrieval_score,
            row.item.get("objectType") == "decision",
        ),
        reverse=True,
    )
    return ranked[:top_k]
