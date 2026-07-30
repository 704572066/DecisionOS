# 007 Context Specification

> **文档编号：** 007
>
> **分类：** Runtime Specification
>
> **状态：** Draft
>
> **版本：** v0.1.0
>
> **最后更新：** 2026-07-30

---

# 1. 文档目的

本文档定义 DecisionOS 的运行时上下文（Context）规范。

Context 是 AI 在某一时刻用于推理、规划和决策的最小业务信息集合（Minimal Business Information Set）。

Context 是 Runtime Layer 的核心对象。

Context 用于组织：

- 当前业务目标；
- 已检索知识；
- 对象关系；
- 外部引用；
- 临时运行数据；
- 推理约束。

Context 是 Runtime View，而不是持久化知识。

---

# 2. 定义

Context 是 Context Session 在某一时刻的运行时快照（Runtime Snapshot）。

Context 表示：

> AI 当前能够看到、理解并参与推理的全部业务信息。

Context 不属于 Knowledge Layer。

Context 由 Runtime 动态构建。

---

# 3. 设计目标

Context 应满足以下目标：

- Minimal（最小化）
- Relevant（高相关）
- Dynamic（动态变化）
- Explainable（可解释）
- AI Native（AI 原生）
- Technology Independent（技术无关）

---

# 4. Context 与 Context Session

Context Session 与 Context 的职责不同。

| Context Session | Context |
|-----------------|----------|
| Runtime Boundary | Runtime View |
| 生命周期容器 | 当前运行快照 |
| 一个 Session 一个 | 一个 Session 可包含多个 |
| 保存 Trace | 不保存 Trace |
| 保存生命周期 | 仅表示当前状态 |

例如：

```text
Session

────────────────────────

Context #1

↓

Tool Search

↓

Context #2

↓

Reasoning

↓

Context #3

↓

Decision
```

Context 会随着运行过程不断变化。

---

# 5. Context 组成

一个 Context 通常包含：

```text
Context
│
├── Intent
├── Knowledge Objects
├── Relationship Graph
├── Runtime Memory
├── External References
├── Constraints
├── Current Objective
└── Retrieved Facts
```

各组成部分共同构成当前推理视图。

---

# 6. Intent

Intent 是当前推理目标。

例如：

- 分析项目延期原因
- 制定市场进入策略
- 汇总客户反馈
- 生成会议决策

Intent 决定 Context 的构建方向。

---

# 7. Knowledge Objects

Context 可以引用多个 Knowledge Object。

例如：

- Meeting
- Project
- Decision
- Task
- Evidence
- Document

Context 不拥有这些对象。

仅保存引用。

---

# 8. Relationship Graph

Context 可以引用 Relationship Graph。

例如：

```text
Project

│

contains

│

Meeting

│

produces

│

Decision

│

creates

│

Task
```

Relationship 为 AI 提供业务语义。

Context 不应复制整个图。

仅保留当前推理所需部分。

---

# 9. Runtime Memory

Runtime Memory 保存：

- 中间结果；
- 当前变量；
- 已完成步骤；
- 最近工具输出；
- 临时事实。

Runtime Memory 生命周期不得超过当前 Context Session。

---

# 10. External References

Context 可以引用外部资源。

例如：

- ERP
- CRM
- Git Repository
- Wiki
- File
- API

外部引用属于 Reference Object。

Context 不复制外部数据。

---

# 11. Constraints

Context 可以包含当前约束。

例如：

- 时间限制；
- 权限限制；
- 成本限制；
- 合规要求；
- 企业策略。

AI 应遵守这些约束完成推理。

---

# 12. Context Builder

Context 应由 Context Builder 自动构建。

典型流程：

```text
Intent

↓

Knowledge Retrieval

↓

Relationship Expansion

↓

Filtering

↓

Ranking

↓

Compression

↓

Context
```

Context Builder 应保证：

- 高相关；
- 最小数据量；
- 最低噪声。

---

# 13. Dynamic Context

Context 是动态变化的。

例如：

```text
Question

↓

Context #1

↓

Tool Search

↓

Context #2

↓

Reasoning

↓

Context #3

↓

Decision
```

随着：

- Tool Calling；
- 用户反馈；
- 新知识产生；

Context 应实时更新。

---

# 14. Context Window

DecisionOS 区分：

```text
Knowledge Layer

↓

Context

↓

Prompt
```

Prompt 是 Context 的一种表达形式。

Context 可以表示为：

- Text
- JSON
- Graph
- Table
- Multi-modal

Prompt 不等于 Context。

---

# 15. Explainability

Context 应支持解释。

AI 输出的每项结论都应能够回答：

- 来源于哪些 Knowledge Object？
- 使用了哪些 Relationship？
- 引用了哪些 Evidence？
- 是否调用了外部工具？

Explainability 是企业级 AI 的核心能力。

---

# 16. Design Principles

Context 应遵循以下原则。

## Minimal

仅包含当前任务需要的信息。

避免无关知识。

---

## Relevant

所有内容应与当前 Intent 相关。

---

## Dynamic

Context 应持续更新。

---

## Traceable

Context 的变化应可追踪。

---

## Technology Independent

Context 不绑定：

- LangChain
- LangGraph
- MCP
- CrewAI
- AutoGen

仅定义运行模型。

---

# 17. Out of Scope

本文档不涉及：

- Prompt Engineering
- RAG 算法
- 向量数据库
- Agent Workflow
- Memory 实现
- 检索排序算法

将在后续规范中定义。

---

# 18. References

- 001 Domain Overview
- 002 Domain Object Model
- 003 Common Object Specification
- 004 Relationship Model
- 005 Knowledge Object Model
- 006 Context Session Specification

---

# 修订记录

| 版本 | 日期 | 内容 |
|------|------|------|
| v0.1.0 | 2026-07-30 | 初始版本 |