# Sprint 2-3.1.1：Reminder TTFT Optimization

## 目标

只优化实时 AI Reminder 的首内容延迟（TTFT），不修改 Context、Retriever、Reranker、Source Guard。

## 改动

1. Chat Completion 请求增加 `enable_thinking`，默认关闭：

```env
REMINDER_ENABLE_THINKING=false
```

2. 第一个 content chunk 到达时发送：

```json
{"type":"reminder.ttft","reminderId":"...","firstContentMs":930.52}
```

3. `reminder.completed` 增加：

```json
{"diagnostics":{"thinkingEnabled":false,"firstContentMs":930.52,"llmTotalMs":6120.44}}
```

4. 前端生成中卡片显示：`首字 931ms`。

## 合并

```bash
python3 scripts/apply_sprint2_3_1_1_patch.py
cat src/frontend/src/style.css.sprint2_3_1_1.append >> src/frontend/src/style.css
rm src/frontend/src/style.css.sprint2_3_1_1.append
```

把 `.env.sprint2_3_1_1.example` 与 Compose patch 合并到生产配置。

## 验收

观察 `firstContentMs` 与 `llmTotalMs`。理想状态是 `firstContentMs` 显著小于完整模型耗时。
