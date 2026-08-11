# Sprint 3-3.1.3 Runtime Risk Lifecycle Patch

基于用户上传的 DecisionOS 最新仓库生成。

## 修改文件

- `src/backend/app/decision_board/engine.py`
- `src/backend/app/runtime/event_extractor.py`
- `src/backend/app/runtime/state_reducer.py`

## 修复目标

1. `decisionFacts.discountPercent` 作为当前折扣事实源。
2. 付款风险与折扣风险独立维护。
3. 付款从 180 天改善到 90 天，只解除 `payment_term`，不会误消除仍存在的 18% 折扣风险。
4. 折扣从 >10% 回到 <=10% 时产生 `RiskResolved(discountPercent)`，写入 `resolvedRisks: ["discount"]`。
5. 折扣再次升到 >10% 时重新打开 `discount` 风险。
6. 付款条件再次恶化时重新打开 `payment_term` 风险。
7. 当 AI reminder 因旧付款条件被过滤时，Decision Board 仍根据 runtime fact 为 >10% 折扣生成兜底风险。

## 验证

已执行：

```bash
python -m compileall -q src/backend/app
```

建议部署后验证：

- 18% + 180天 -> 两类风险存在
- 18% + 90天 -> payment_term 解除，但 18% 折扣风险仍存在
- 8% + 90天 -> discount 解除
- 18% + 90天 -> discount 重新打开
