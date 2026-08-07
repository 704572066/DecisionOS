# Sprint 2-1.3：Canonical Business Statement

目标：作为 Context Builder 预处理的最后一层，将多个相似、重复、残缺的业务句收敛为稳定的 Canonical Business Statement。

当前示例应从三条清洗句收敛为：

```text
客户要求整体价格下降18%，并希望付款周期延长到180天。
```

设计原则：不使用 LLM；不修改原始 Meeting transcript；只作用于 cleanTranscriptWindow；只根据确定事实生成规范句；无关但有价值的独立业务陈述继续保留。

新增：`src/backend/app/context/canonicalizer.py`

合并后执行：

```bash
python3 scripts/apply_sprint2_1_3_patch.py
```

Builder 版本升级为 `context-builder-v0.1.3`，新增 `coveredSentences`、`canonicalStatements`。

无需数据库迁移。完成本版本后冻结 Context preprocessing，进入 Sprint 2-2 Retriever。
