from __future__ import annotations

import re
from dataclasses import dataclass
from difflib import SequenceMatcher

_SPLIT = re.compile(r"(?<=[。！？!?；;])|\n+")
_SPACE = re.compile(r"\s+")
_PUNCT = re.compile(r"[，。！？；：、,.!?;:\s]+")
_PERCENT_NOISE = re.compile(r"(?:100\s*分|百分之)\s*(\d+(?:\.\d+)?)\s*%?")
_PERCENT_WORD = re.compile(r"百分之\s*(\d+(?:\.\d+)?)")
_MEASUREMENT = re.compile(r"\d+(?:\.\d+)?(?:%|天|个月|月|周|小时|元|万元|万|亿元)")

_FILLER = {
    "然后", "我自己", "你好", "是什么", "空间", "出去", "有研究吗",
    "有一天啊", "嗯", "啊", "呃", "哦", "好的", "行", "可以",
}

_SAFE_REPLACEMENTS = {
    "副感周期": "付款周期",
    "付感周期": "付款周期",
    "变以希望": "并希望",
    "电影希望": "并希望",
    "客服要求": "客户要求",
}

_SUBJECT_TERMS = ("客户", "甲方", "采购方", "供应商", "项目", "公司", "集团")
_ACTION_TERMS = (
    "要求", "希望", "提出", "需要", "计划", "决定", "同意", "拒绝",
    "降低", "下降", "提高", "延长", "缩短", "交付", "付款", "签约",
)
_BUSINESS_TERMS = (
    "客户", "价格", "整体价格", "降价", "折扣", "报价", "付款", "账期",
    "付款周期", "利润", "毛利", "交付", "合同", "风险", "逾期", "担保",
    "项目", "签约", "验收",
)
_CONNECTORS = ("并", "且", "同时", "以及", "另外", "还", "希望", "要求")


@dataclass(slots=True)
class CleanTranscriptResult:
    raw_text: str
    clean_text: str
    raw_segments: int
    clean_segments: int
    removed_segments: int
    merged_segments: int
    replacements: int
    consolidated_sentences: int
    incomplete_segments: int

    def metadata(self) -> dict:
        return {
            "rawSegments": self.raw_segments,
            "cleanSegments": self.clean_segments,
            "removedSegments": self.removed_segments,
            "mergedSegments": self.merged_segments,
            "replacements": self.replacements,
            "consolidatedSentences": self.consolidated_sentences,
            "incompleteSegments": self.incomplete_segments,
        }


def clean_transcript(text: str) -> CleanTranscriptResult:
    raw = (text or "").replace("\r\n", "\n").strip()
    raw_segments = [part.strip() for part in _SPLIT.split(raw) if part and part.strip()]

    normalized: list[str] = []
    removed = 0
    replacements = 0
    incomplete = 0

    for segment in raw_segments:
        segment, replacement_count = _normalize_segment(segment)
        replacements += replacement_count

        if not segment or _is_noise(segment):
            removed += 1
            continue

        if _is_incomplete(segment):
            incomplete += 1
            # Keep incomplete segments only when they can plausibly complete a
            # neighbouring business sentence. Standalone fragments are dropped.
            if not _can_be_continuation(segment):
                removed += 1
                continue

        normalized.append(segment)

    deduplicated: list[str] = []
    merged = 0
    for segment in normalized:
        if not deduplicated:
            deduplicated.append(segment)
            continue

        merged_value = _merge_similar(deduplicated[-1], segment)
        if merged_value is not None:
            deduplicated[-1] = merged_value
            merged += 1
            continue

        recent_index = _recent_duplicate(deduplicated, segment)
        if recent_index is not None:
            deduplicated[recent_index] = _prefer_complete(
                deduplicated[recent_index], segment
            )
            merged += 1
            continue

        deduplicated.append(segment)

    consolidated, consolidated_count = _consolidate_business_sentences(deduplicated)

    return CleanTranscriptResult(
        raw_text=raw,
        clean_text="\n".join(consolidated).strip(),
        raw_segments=len(raw_segments),
        clean_segments=len(consolidated),
        removed_segments=removed,
        merged_segments=merged,
        replacements=replacements,
        consolidated_sentences=consolidated_count,
        incomplete_segments=incomplete,
    )


def _normalize_segment(text: str) -> tuple[str, int]:
    value = _SPACE.sub(" ", text).strip("，,；; ")
    replacements = 0

    for wrong, right in _SAFE_REPLACEMENTS.items():
        count = value.count(wrong)
        if count:
            value = value.replace(wrong, right)
            replacements += count

    # Observed ASR output: "100分18%" should represent "18%".
    value, count = _PERCENT_NOISE.subn(lambda m: f"{m.group(1)}%", value)
    replacements += count

    value, count = _PERCENT_WORD.subn(lambda m: f"{m.group(1)}%", value)
    replacements += count

    return value.strip(), replacements


def _is_noise(text: str) -> bool:
    fingerprint = _fingerprint(text)
    if not fingerprint or text in _FILLER:
        return True

    business_score = _business_information_score(text)

    if len(fingerprint) <= 2 and not _MEASUREMENT.search(text):
        return True

    # Long conversational fragments with no measurable fact, business concept,
    # subject or action are still noise.
    if business_score == 0:
        return True

    return False


def _business_information_score(text: str) -> int:
    score = 0
    score += 2 if _MEASUREMENT.search(text) else 0
    score += min(2, sum(1 for term in _BUSINESS_TERMS if term in text))
    score += 1 if any(term in text for term in _SUBJECT_TERMS) else 0
    score += 1 if any(term in text for term in _ACTION_TERMS) else 0
    return score


def _is_incomplete(text: str) -> bool:
    fp = _fingerprint(text)
    has_subject = any(term in text for term in _SUBJECT_TERMS)
    has_action = any(term in text for term in _ACTION_TERMS)
    has_measurement = bool(_MEASUREMENT.search(text))

    if len(fp) < 6 and not (has_subject and has_action):
        return True

    # Examples: "下降18%" or "客户要求整体价格".
    if has_measurement and not has_subject and len(fp) <= 8:
        return True
    if has_subject and not has_action and not has_measurement and len(fp) <= 12:
        return True

    return False


def _can_be_continuation(text: str) -> bool:
    return (
        text.startswith(_CONNECTORS)
        or bool(_MEASUREMENT.search(text))
        or any(term in text for term in ("下降", "延长", "缩短", "交付", "付款"))
    )


def _merge_similar(previous: str, current: str) -> str | None:
    a = _fingerprint(previous)
    b = _fingerprint(current)

    if a == b or a.startswith(b) or b.startswith(a):
        return _prefer_complete(previous, current)

    if min(len(a), len(b)) >= 8 and SequenceMatcher(None, a, b).ratio() >= 0.88:
        return _prefer_complete(previous, current)

    return None


def _recent_duplicate(values: list[str], candidate: str) -> int | None:
    b = _fingerprint(candidate)
    for index in range(len(values) - 1, max(-1, len(values) - 8), -1):
        a = _fingerprint(values[index])
        if a == b:
            return index
        if min(len(a), len(b)) >= 8 and SequenceMatcher(None, a, b).ratio() >= 0.90:
            return index
    return None


def _consolidate_business_sentences(values: list[str]) -> tuple[list[str], int]:
    result: list[str] = []
    consolidated = 0
    index = 0

    while index < len(values):
        current = values[index]

        if index + 1 < len(values):
            next_value = values[index + 1]
            combined = _combine_if_related(current, next_value)
            if combined is not None:
                result.append(combined)
                consolidated += 1
                index += 2
                continue

        # Drop a remaining incomplete fragment when a more complete equivalent
        # has already been retained.
        if _is_incomplete(current):
            similar_index = _recent_duplicate(result, current)
            if similar_index is not None:
                result[similar_index] = _prefer_complete(
                    result[similar_index], current
                )
                consolidated += 1
                index += 1
                continue

        result.append(_ensure_terminal_punctuation(current))
        index += 1

    # Final semantic duplicate pass after sentence consolidation.
    compact: list[str] = []
    for sentence in result:
        duplicate_index = _recent_duplicate(compact, sentence)
        if duplicate_index is None:
            compact.append(sentence)
        else:
            compact[duplicate_index] = _prefer_complete(
                compact[duplicate_index], sentence
            )
            consolidated += 1

    return compact, consolidated


def _combine_if_related(first: str, second: str) -> str | None:
    first_topics = _topic_signature(first)
    second_topics = _topic_signature(second)

    # Typical meeting pair:
    # 客户要求整体价格下降18%
    # 并希望付款周期延长到180天
    if (
        first_topics
        and second_topics
        and (
            second.startswith(_CONNECTORS)
            or bool(first_topics & second_topics)
            or ("客户" in first and any(x in second for x in ("付款", "交付", "合同")))
        )
    ):
        first_clean = first.rstrip("。！？；,， ")
        second_clean = second.lstrip("，, ")
        if second_clean.startswith(("并", "且", "同时", "以及")):
            return _ensure_terminal_punctuation(f"{first_clean}，{second_clean}")
        return _ensure_terminal_punctuation(f"{first_clean}，{second_clean}")

    # A short measurable fragment can complete the preceding sentence.
    if _is_incomplete(second) and _MEASUREMENT.search(second):
        return _ensure_terminal_punctuation(
            f"{first.rstrip('。！？；,， ')}，{second.lstrip('，, ')}"
        )

    return None


def _topic_signature(text: str) -> set[str]:
    mapping = {
        "价格": ("价格", "降价", "折扣", "报价", "下降"),
        "付款": ("付款", "账期", "周期", "回款"),
        "交付": ("交付", "验收", "上线", "延期"),
        "合同": ("合同", "签约", "条款"),
        "风险": ("风险", "逾期", "坏账", "担保"),
        "客户": ("客户", "甲方", "采购方"),
    }
    return {
        topic
        for topic, terms in mapping.items()
        if any(term in text for term in terms)
    }


def _prefer_complete(first: str, second: str) -> str:
    return second if _completeness_score(second) >= _completeness_score(first) else first


def _completeness_score(text: str) -> tuple[int, int, int, int]:
    return (
        _business_information_score(text),
        len(_MEASUREMENT.findall(text)),
        len(_topic_signature(text)),
        len(_fingerprint(text)),
    )


def _ensure_terminal_punctuation(text: str) -> str:
    value = text.strip()
    if not value:
        return value
    return value if value.endswith(("。", "！", "？", ";", "；")) else value + "。"


def _fingerprint(text: str) -> str:
    return _PUNCT.sub("", text).lower()
