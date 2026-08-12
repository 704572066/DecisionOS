# Sprint 3-3.2 Decision Board Simplification

本次修改基于用户提供的最新仓库版本，目标是降低实时会议面板噪音，并让“当前关注”更接近当前 Runtime 状态。

## 修改范围

1. 移除 Decision Signal 的前端展示和 DecisionBoard API 字段。
2. 移除 LATER / 待确认的前端展示和 DecisionBoard API `todos` 字段。
3. 面板只保留当前目标/状态/成熟度、当前关注、下一步行动、提醒/依据入口。
4. 当前折扣风险解除后，过滤仍引用旧折扣条件的 reminder risk/action；折扣重新超过 10% 时仍由 Runtime 当前事实兜底恢复价格风险。
5. `currentConditions`、`recentEvents`、`resolvedRisks` 继续保留在后端，供 Runtime 状态与后续诊断使用。

## 本次未修改

- `event_extractor.py` 的语义覆盖范围。
- Semantic/LLM Event Extractor。
- Runtime recentEvents/resolvedRiskKeys 状态机制。

后续应单独推进 Semantic Decision Event Layer，避免继续通过增加正则覆盖自然语言输入。
