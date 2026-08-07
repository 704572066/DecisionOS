from __future__ import annotations

import re
from dataclasses import dataclass

_PERCENT = re.compile(r"(\d+(?:\.\d+)?)\s*%")
_DURATION = re.compile(r"(\d+)\s*(天|个月|月|周|小时)")
_PRICE_TERMS = ("价格", "降价", "折扣", "报价", "下降")
_PAYMENT_TERMS = ("付款", "账期", "付款周期", "回款")
_DELIVERY_TERMS = ("交付", "验收", "上线", "延期")
_CUSTOMER_TERMS = ("客户", "甲方", "采购方")


@dataclass(slots=True)
class CanonicalizationResult:
    statements: list[str]
    covered_sentences: int
    canonical_statements: int

    def metadata(self) -> dict:
        return {
            "coveredSentences": self.covered_sentences,
            "canonicalStatements": self.canonical_statements,
        }


def canonicalize_business_statements(sentences: list[str]) -> CanonicalizationResult:
    values = [s.strip() for s in sentences if s and s.strip()]
    if not values:
        return CanonicalizationResult([], 0, 0)

    canonical: list[str] = []
    consumed: set[int] = set()

    price = _best_percentage(values, _PRICE_TERMS)
    payment = _best_duration(values, _PAYMENT_TERMS)

    if price and payment:
        statement = f"客户要求整体价格下降{price}，并希望付款周期延长到{payment}。"
        canonical.append(statement)
        for index, sentence in enumerate(values):
            if _covered_by_price_payment(sentence, price, payment):
                consumed.add(index)

    for index, sentence in enumerate(values):
        if index in consumed:
            continue
        if _is_fragment_covered_by(canonical, sentence):
            consumed.add(index)
            continue
        canonical.append(_ensure_period(sentence))

    canonical = _semantic_dedupe(canonical)
    return CanonicalizationResult(
        statements=canonical,
        covered_sentences=len(consumed),
        canonical_statements=len(canonical),
    )


def _best_percentage(values: list[str], topic_terms: tuple[str, ...]) -> str | None:
    candidates: list[tuple[int, str]] = []
    for sentence in values:
        if not any(term in sentence for term in topic_terms):
            continue
        match = _PERCENT.search(sentence)
        if match:
            candidates.append((_sentence_score(sentence), f"{match.group(1)}%"))
    return max(candidates, default=(0, None), key=lambda x: x[0])[1]


def _best_duration(values: list[str], topic_terms: tuple[str, ...]) -> str | None:
    candidates: list[tuple[int, str]] = []
    for sentence in values:
        if not any(term in sentence for term in topic_terms):
            continue
        match = _DURATION.search(sentence)
        if match:
            candidates.append((_sentence_score(sentence), f"{match.group(1)}{match.group(2)}"))
    return max(candidates, default=(0, None), key=lambda x: x[0])[1]


def _sentence_score(sentence: str) -> int:
    score = len(sentence)
    score += 20 if any(x in sentence for x in _CUSTOMER_TERMS) else 0
    score += 20 if any(x in sentence for x in ("要求", "希望", "提出")) else 0
    score += 10 if _PERCENT.search(sentence) else 0
    score += 10 if _DURATION.search(sentence) else 0
    return score


def _covered_by_price_payment(sentence: str, price: str, payment: str) -> bool:
    has_business = any(term in sentence for term in (*_PRICE_TERMS, *_PAYMENT_TERMS, *_CUSTOMER_TERMS))
    if not has_business:
        return False
    price_value = price.rstrip("%")
    has_price_fact = price_value in sentence and "%" in sentence
    has_payment_fact = payment in sentence
    is_fragment = len(sentence) <= 24
    return has_price_fact or has_payment_fact or is_fragment


def _is_fragment_covered_by(canonical: list[str], sentence: str) -> bool:
    compact = _compact(sentence)
    if not compact:
        return True
    for target in canonical:
        target_compact = _compact(target)
        if compact in target_compact:
            return True
        if len(compact) <= 14:
            overlap = sum(1 for token in _tokens(sentence) if token in target)
            if overlap >= 2:
                return True
    return False


def _semantic_dedupe(values: list[str]) -> list[str]:
    result: list[str] = []
    for value in values:
        if not any(_compact(value) == _compact(existing) for existing in result):
            result.append(value)
    return result


def _tokens(text: str) -> list[str]:
    tokens = []
    for term in (*_PRICE_TERMS, *_PAYMENT_TERMS, *_DELIVERY_TERMS, *_CUSTOMER_TERMS, "要求", "希望"):
        if term in text:
            tokens.append(term)
    tokens.extend(_PERCENT.findall(text))
    tokens.extend("".join(x) for x in _DURATION.findall(text))
    return tokens


def _compact(text: str) -> str:
    return re.sub(r"[，。！？；：、,.!?;:\s]+", "", text)


def _ensure_period(text: str) -> str:
    value = text.strip()
    return value if value.endswith(("。", "！", "？")) else value + "。"
