from __future__ import annotations
import re
from dataclasses import dataclass
from difflib import SequenceMatcher

_SPLIT = re.compile(r"(?<=[。！？!?；;])|\n+")
_SPACE = re.compile(r"\s+")
_PUNCT = re.compile(r"[，。！？；：、,.!?;:\s]+")
_FILLER = {"然后","我自己","你好","是什么","空间","出去","有研究吗","有一天啊"}
_REPLACE = {"副感周期":"付款周期","付感周期":"付款周期","变以希望":"并希望","电影希望":"并希望","客服要求":"客户要求"}
_SIGNALS = ("客户","价格","降价","折扣","付款","账期","周期","利润","交付","合同","风险","项目")

@dataclass(slots=True)
class CleanTranscriptResult:
    raw_text: str
    clean_text: str
    raw_segments: int
    clean_segments: int
    removed_segments: int
    merged_segments: int
    replacements: int
    def metadata(self) -> dict:
        return {
            "rawSegments": self.raw_segments,
            "cleanSegments": self.clean_segments,
            "removedSegments": self.removed_segments,
            "mergedSegments": self.merged_segments,
            "replacements": self.replacements,
        }

def clean_transcript(text: str) -> CleanTranscriptResult:
    raw = (text or "").replace("\r\n", "\n").strip()
    parts = [x.strip() for x in _SPLIT.split(raw) if x and x.strip()]
    cleaned, removed, replacements = [], 0, 0
    for part in parts:
        for wrong, right in _REPLACE.items():
            count = part.count(wrong)
            if count:
                part = part.replace(wrong, right)
                replacements += count
        part = _SPACE.sub(" ", part).strip("，,；; ")
        if _is_noise(part):
            removed += 1
            continue
        cleaned.append(part)

    result, merged = [], 0
    for part in cleaned:
        if not result:
            result.append(part)
            continue
        merged_value = _merge(result[-1], part)
        if merged_value is None:
            recent = _recent_duplicate(result, part)
            if recent is None:
                result.append(part)
            else:
                result[recent] = _prefer(result[recent], part)
                merged += 1
        else:
            result[-1] = merged_value
            merged += 1

    return CleanTranscriptResult(
        raw_text=raw,
        clean_text="\n".join(result).strip(),
        raw_segments=len(parts),
        clean_segments=len(result),
        removed_segments=removed,
        merged_segments=merged,
        replacements=replacements,
    )

def _fingerprint(text: str) -> str:
    return _PUNCT.sub("", text).lower()

def _is_noise(text: str) -> bool:
    fp = _fingerprint(text)
    if not fp or text in _FILLER:
        return True
    if len(fp) <= 2 and not any(ch.isdigit() for ch in fp):
        return True
    if len(fp) <= 5:
        return not (
            any(term in text for term in _SIGNALS)
            or bool(re.search(r"\d+(?:\.\d+)?(?:%|天|月|元|万)", text))
        )
    return False

def _merge(previous: str, current: str) -> str | None:
    a, b = _fingerprint(previous), _fingerprint(current)
    if a == b or a.startswith(b) or b.startswith(a):
        return _prefer(previous, current)
    if min(len(a), len(b)) >= 8 and SequenceMatcher(None, a, b).ratio() >= 0.88:
        return _prefer(previous, current)
    return None

def _recent_duplicate(values: list[str], candidate: str) -> int | None:
    b = _fingerprint(candidate)
    for index in range(len(values)-1, max(-1, len(values)-8), -1):
        a = _fingerprint(values[index])
        if a == b or (min(len(a),len(b)) >= 8 and SequenceMatcher(None,a,b).ratio() >= 0.9):
            return index
    return None

def _prefer(a: str, b: str) -> str:
    def score(value: str):
        return (
            len(re.findall(r"\d+(?:\.\d+)?(?:%|天|月|元|万)", value)),
            sum(1 for term in _SIGNALS if term in value),
            len(_fingerprint(value)),
        )
    return b if score(b) >= score(a) else a
