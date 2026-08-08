# Sprint 3-1：Reminder → Decision Candidate

目标：AI Reminder → 运行时 Decision Candidate → 用户编辑/确认 → 正式 Decision → KnowledgeItem。

Candidate 不新增数据库表；它只是正式 Decision 被确认前的运行时草案。

## API
- `POST /api/decisions/meetings/{meetingId}/candidate`
- `POST /api/decisions/confirm`

Candidate Evidence 不直接信任浏览器内容，服务端重新执行 Context → Hybrid Retriever → Reranker 后，按 Reminder source IDs 选择可信 Evidence。

确认后复用现有 `Decision`、`KnowledgeItem`，并把 candidateId/contextId/reasons/risks/evidence 快照写入 `evidence_summary`。

前端 Reminder 卡新增“生成决策”，打开可编辑的 Decision Draft；只有点击“确认决策”才落库。
