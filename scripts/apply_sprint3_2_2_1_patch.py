#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
service = ROOT / "src/backend/app/runtime/service.py"
text = service.read_text(encoding="utf-8")

if "import re\n" not in text:
    marker = "from __future__ import annotations\n"
    if marker not in text:
        raise SystemExit("runtime/service.py future import marker not found")
    text = text.replace(marker, marker + "\nimport re\n", 1)

old = "            decisionFacts=dict(previous.decisionFacts) if previous else {},\n"
new = """            decisionFacts=(
                dict(previous.decisionFacts)
                if previous
                else self._decision_facts_from_context(context)
            ),
"""
if new not in text:
    if old not in text:
        raise SystemExit("decisionFacts initialization marker not found")
    text = text.replace(old, new, 1)

if "def _decision_facts_from_context(" not in text:
    marker = """    @staticmethod
    def _latest_final_segment_text(
"""
    helper = '''    @staticmethod
    def _decision_facts_from_context(context: dict) -> dict:
        output: dict = {}
        canonical = (
            context.get("cleanTranscriptWindow")
            or context.get("transcriptWindow")
            or ""
        )

        for fact in context.get("facts") or []:
            fact_type = fact.get("factType") or ""
            value = fact.get("normalizedValue") or fact.get("text") or ""

            if (
                fact_type == "percentage"
                and any(
                    term in canonical
                    for term in ("降价", "折扣", "优惠", "价格下降", "价格下调")
                )
            ):
                match = re.search(r"(\\d+(?:\\.\\d+)?)\\s*%", str(value))
                if match:
                    output["discountPercent"] = float(match.group(1))

            if (
                fact_type == "duration"
                and any(
                    term in canonical
                    for term in ("付款", "账期", "回款")
                )
            ):
                match = re.search(r"(\\d+)\\s*天", str(value))
                if match:
                    output["paymentTermDays"] = int(match.group(1))

        return output

'''
    if marker not in text:
        raise SystemExit("_latest_final_segment_text marker not found")
    text = text.replace(marker, helper + marker, 1)

service.write_text(text, encoding="utf-8")
print("Sprint 3-2.2.1 Runtime Fact Bootstrap applied:", service)
