# Sprint 2-3.1：Streaming AI Reminder

继续使用现有 Meeting WebSocket，不引入 SSE。

## WebSocket 事件

- `reminder.started`
- `reminder.delta`
- `reminder.completed`
- `reminder.failed`

`delta` 只展示 title / summary / suggestion / reason。
sources/confidence 必须等最终 JSON 完成并通过 Source Guard 后才发送。

## 解耦

final transcript 持久化后不再等待 LLM 完成，而是用 `asyncio.create_task`
启动 Streaming Reminder，因此录音/转写链路不会被 7 秒模型请求占住。

## 合并

```bash
python3 scripts/apply_sprint2_3_1_patch.py
cat src/frontend/src/style.css.sprint2_3_1.append >> src/frontend/src/style.css
rm src/frontend/src/style.css.sprint2_3_1.append
```

然后重新构建 backend + frontend。

## 验收

说出：

```text
客户要求整体价格下降18%，并希望付款周期延长到180天。
```

预期：先出现 `AI 生成中…`，随后 title/summary/suggestion/reason 增量出现；
模型完成后临时卡消失，正式带 Evidence 的 Reminder 卡出现。
