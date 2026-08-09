# Sprint 3-2.2：Event Extractor + Runtime State Update

## 目标

让 Decision Board 从“每次重新读整段会议”升级为能理解关键业务条件的变化。

```text
Final Transcript
      ↓
Event Extractor
      ↓
DecisionEvent
      ↓
Runtime State Reducer
      ↓
Decision Board
```

## 第一版事件

仅支持：

- PriceChanged
- PaymentTermChanged
- ConditionAccepted
- ConditionRejected
- ConstraintAdded
- RiskResolved

这些都是 Runtime Event，不新增数据库表、不新增长期领域对象。

## Runtime State 新增

```json
{
  "decisionFacts": {
    "discountPercent": 18,
    "paymentTermDays": 90
  },
  "recentEvents": [],
  "resolvedRiskKeys": []
}
```

## 实时更新

每个 final transcript 保存后执行轻量：

```text
extract event
→ reduce Runtime State
```

不调用 Embedding，不调用 LLM。

例如：

```text
客户同意把付款周期调整到90天。
```

得到：

```json
[
  {
    "type": "PaymentTermChanged",
    "previousValue": 180,
    "value": 90
  },
  {
    "type": "RiskResolved",
    "field": "paymentTermDays"
  }
]
```

Board 会隐藏仍然描述旧 180 天条件的付款风险。

## decisionReadiness

原来的：

```json
"confidence": 97
```

改为：

```json
"decisionReadiness": 97
```

它表示信息成熟度，不表示 AI 有 97% 概率判断正确。

## Claim Guard

第一版明确保护：

```text
折扣率 != 毛利率
```

因此：

```text
18%折扣触发 >10% 折扣评估规则
```

可以确定。

但：

```text
18%折扣直接突破18%毛利率
```

会被修正为：

```text
折扣可能影响目标毛利率，需要结合成本进一步测算。
```

## 验收

先获得当前 Board：

```bash
curl http://127.0.0.1/api/decision-board/<meetingId>
```

然后在会议里增加：

```text
客户同意把付款周期调整到90天。
```

再次：

```bash
curl http://127.0.0.1/api/decision-board/<meetingId>
```

目标：

```json
{
  "currentConditions": {
    "paymentTermDays": 90
  },
  "resolvedRisks": ["payment_term"]
}
```

旧的 180 天付款风险不再出现在 `risks`。

如果直接使用已有历史会议测试，也可以追加 transcript 后调用：

```bash
curl -X POST \
  http://127.0.0.1/api/decision-board/<meetingId>/refresh
```

查看 `recentEvents`。
