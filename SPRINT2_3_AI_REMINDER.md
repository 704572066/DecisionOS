# Sprint 2-3：Context-aware Reranker + Prompt Builder + AI Reminder

## 目标

把已经跑通的实时会议、Context Builder v0.1.3 和 Hybrid Retriever 正式连接成 AI Reminder：

```text
Realtime Transcript
      ↓
Context Builder v0.1.3
      ↓
Hybrid Retriever
      ↓
Context-aware Reranker
      ↓
Top 3~5 Evidence
      ↓
Prompt Builder
      ↓
OpenAI-compatible LLM
      ↓
Structured AI Reminder
      ↓
WebSocket reminder.batch
```

## 新模块

```text
src/backend/app/intelligence/
├── models.py
├── reranker.py
├── prompt_builder.py
├── llm.py
└── reminder_engine.py
```

## Context-aware Reranker

在 Hybrid Retriever 的 score 基础上增加当前业务上下文权重：

- `currentObjective`
- topics
- facts
- Decision / Evidence / Document 类型
- 价格 / 付款 / 利润 / 风险 / policy 关系

例如当前目标是“在保证利润率的前提下完成签约”，则包含毛利率、折扣边界、付款规则的 Evidence 会获得额外权重。

## Prompt Builder

Prompt 被拆成明确的：

```text
System Policy
Current Objective
Canonical Meeting Context
Top Evidence
JSON Output Contract
```

要求模型：

- 不得虚构企业事实；
- 最多输出 3 条提醒；
- 每条 Reminder 必须引用至少一个 Retriever Evidence；
- 不替管理者做最终 Decision；
- 只返回 JSON。

## Reminder 输出

```json
{
  "type": "risk",
  "title": "价格与账期组合风险",
  "summary": "当前18%降价与180天账期形成组合风险。",
  "suggestion": "优先缩短账期；若保持长账期，应重新评估折扣或增加担保。",
  "reason": "历史规则显示较高折扣需要评估付款周期，长账期需增加风险控制。",
  "sources": [
    {
      "type": "policy",
      "id": "knowledge-...",
      "title": "公司项目利润率规则",
      "score": 0.88
    }
  ],
  "confidence": 0.88
}
```

同时保留 Sprint 1 前端兼容字段：

```text
source
relevanceScore
```

## Source Guard

LLM 返回的 source 不会直接信任。

后端会检查：

```text
LLM source id
      ↓
是否存在于本次 Reranked Evidence
      ↓
是 → 保留
否 → 删除
```

没有任何合法 Evidence source 的 AI Reminder 不会发送。

## 降级机制

LLM 未配置或调用失败时：

```text
generationMode = evidence-fallback
```

系统根据 Reranked Evidence 直接生成可追溯提醒。

LLM 正常时：

```text
generationMode = llm
```

因此 LLM 故障不会影响语音转写和会议数据保存。

## 新 API

```http
POST /api/reminders/meetings/{meetingId}/generate
```

用于独立验证完整链路。

返回：

```text
context
retrieval
rerankedEvidence
reminders
diagnostics
```

`diagnostics` 包括：

```text
generationMode
llmConfigured
llmError
contextMs
retrievalMs
rerankMs
llmMs
totalMs
```

## 实时 Reminder

`RealtimeReminderCoordinator.analyze_if_due()` 已改为 async。

原本：

```python
result = realtime_reminder_coordinator.analyze_if_due(...)
```

变为：

```python
result = await realtime_reminder_coordinator.analyze_if_due(...)
```

网络调用期间不持有内部 RLock，避免一个会议的 Embedding/LLM 延迟阻塞其他会议。

## 配置

```env
OPENAI_BASE_URL=
OPENAI_API_KEY=
OPENAI_MODEL=

LLM_TIMEOUT_SECONDS=30
LLM_JSON_MODE=false
REMINDER_TEMPERATURE=0.1
REMINDER_RETRIEVAL_TOP_K=8
REMINDER_EVIDENCE_TOP_K=5
```

如果当前 OpenAI-compatible 服务支持 JSON mode，可以设置：

```env
LLM_JSON_MODE=true
```

如果不支持保持 `false`，代码仍会从文本中解析 JSON object。

## 合并

```bash
python3 scripts/apply_sprint2_3_patch.py
python3 scripts/apply_frontend_sprint2_3_patch.py

cat src/frontend/src/style.css.sprint2_3.append   >> src/frontend/src/style.css

rm src/frontend/src/style.css.sprint2_3.append
```

将 `.env.sprint2_3.example` 和 `docker-compose.prod.sprint2_3.patch.yml` 中配置合并到当前生产环境。

## 验收顺序

### 1. 独立调用 AI Reminder

```bash
curl -X POST   http://127.0.0.1/api/reminders/meetings/meeting-83e6181f64c7/generate
```

第一步重点看：

```text
rerankedEvidence
```

确认利润率规则、付款历史、历史 Decision 的排序符合当前 Context。

第二步看：

```text
diagnostics.generationMode
```

期望：

```text
llm
```

如果为：

```text
evidence-fallback
```

查看 `diagnostics.llmError`。

### 2. 实时语音

开始会议，讲话：

```text
客户要求整体价格下降18%，并希望付款周期延长到180天。
```

预期实时出现带：

```text
风险
建议
依据
来源
```

的 Reminder。

## Sprint 边界

本 Sprint：

- 不自动创建 Decision；
- 不自动修改 Knowledge；
- 不引入 Agent；
- 不引入 Workflow Engine；
- AI 只提供 Reminder / Evidence / Context；
- 管理者仍负责最终决策。
