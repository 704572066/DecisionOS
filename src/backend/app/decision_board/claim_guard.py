from __future__ import annotations

import re


class ClaimGuard:
    """Minimal deterministic guard for known cross-metric overclaims."""

    def sanitize_risk(self, title: str, summary: str) -> tuple[str, str]:
        combined = title + " " + summary

        # Discount % and margin % cannot be directly compared even when both
        # happen to be 18%. Keep the supported rule relation and require a
        # margin calculation for the downstream impact.
        if (
            ("降价" in combined or "折扣" in combined)
            and ("毛利率" in combined or "利润率" in combined)
        ):
            title = re.sub(
                r"(?:突破|触碰|跌破|低于).*?(?:利润率|毛利率)(?:底线)?",
                "触发折扣评估规则并可能影响目标毛利率",
                title,
            )
            summary = (
                "当前折扣要求需要按公司折扣规则进行评估；"
                "折扣会影响项目利润，但折扣率不能直接等同或比较为毛利率。"
                "是否满足目标毛利率需要结合项目成本进一步测算。"
            )

        return title, summary


claim_guard = ClaimGuard()
