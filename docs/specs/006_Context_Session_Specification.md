# 006 Context Session Specification

> **文档编号：** 006
>
> **分类：** Runtime Specification
>
> **状态：** Draft
>
> **版本：** v0.1.0
>
> **最后更新：** 2026-07-29

---

# 1. 文档目的

本文档定义 DecisionOS 的运行时上下文会话（Context Session）规范。

Context Session 是一次完整企业决策活动的运行时边界（Runtime Boundary）。

它负责组织：

- 用户意图
- 企业知识
- Context 构建
- AI 推理
- 工具调用
- 决策生成
- 知识沉淀

所有运行时对象（Runtime Object）均属于某一个 Context Session。

---

# 2. 定义

Context Session 是一次企业决策过程的完整运行实例。

它始于一个明确的业务目标。

终于：

- 任务完成；
- 用户取消；
- 超时结束；
- 系统异常。

Context Session 是 Runtime Layer 的最高级对象。

---

# 3. 设计目标

Context Session 应满足：

- Runtime Isolation（运行隔离）
- Business Traceability（业务可追溯）
- AI Native（AI 原生）
- Multi-Agent Ready（支持多 Agent）
- Tool Friendly（支持工具调用）
- Recoverable（支持恢复）
- Auditable（支持审计）

---

# 4. 生命周期

Context Session 生命周期如下：

```text
Created
    │
Collecting Context
    │
Planning
    │
Reasoning
    │
Generating Result
    │
Persisting Knowledge
    │
Completed
```

异常状态：

```text
Created
    │
Failed
```

或：

```text
Created
    │
Cancelled
```

生命周期必须完整记录。

---

# 5. Runtime Boundary

Context Session 是所有 Runtime Object 的容器。

```text
Context Session
│
├── Context
├── Prompt
├── Tool Call
├── AI Response
├── Trace
├── Temporary Memory
└── Runtime Metadata
```

Runtime Object 不应脱离 Context Session 独立存在。

---

# 6. Context Session 组成

一个 Context Session 通常包含：

## Session Metadata

包括：

- Session ID
- 创建时间
- 创建者
- 当前状态
- Runtime Version

---

## User Intent

描述本次业务目标。

例如：

> "分析本季度项目延期原因"

Intent 应作为整个推理过程的最高目标。

---

## Context

由 Context Builder 动态生成。

包括：

- Meeting
- Project
- Decision
- Evidence
- Document
- Relationship

Context 不属于持久知识。

---

## Tool Calls

运行期间所有工具调用。

例如：

- Search
- Database
- MCP
- API
- File System

应完整记录。

---

## AI Responses

保存：

- 中间推理结果
- 最终输出
- 总结

便于追溯。

---

## Runtime Trace

记录：

- 每一步执行过程
- Tool 调用
- Prompt 变化
- Context 更新

Trace 用于调试和审计。

---

## Generated Knowledge

运行结束后：

部分结果可以转化为：

- Meeting
- Decision
- Task
- Evidence

成为新的 Knowledge Object。

---

# 7. 与 Knowledge Layer 的关系

Context Session 不保存企业知识。

它引用已有 Knowledge Object。

```text
Knowledge Layer

Meeting
Project
Decision
Document
Evidence

        │
        │ Retrieve
        ▼

Context Session

        │
        ▼

Reasoning

        │
Persist

        ▼

New Knowledge Object
```

Knowledge Layer 与 Runtime Layer 应保持解耦。

---

# 8. Context 构建

Context Session 应通过 Context Builder 构建上下文。

输入：

- User Intent
- Knowledge Objects
- Relationship Graph
- External References

输出：

Context。

Context 应尽可能保持最小化。

避免：

- 全量加载；
- 重复信息；
- 无关知识。

---

# 9. Multi-Agent

一个 Context Session 可以包含多个 Agent。

例如：

```text
Context Session

├── Planner Agent
├── Search Agent
├── Analysis Agent
├── Decision Agent
└── Review Agent
```

多个 Agent 应共享：

- Context
- Trace
- Session Metadata

而不是各自维护独立上下文。

---

# 10. Tool Calling

Tool Call 属于 Runtime Object。

包括：

- 调用时间
- 输入
- 输出
- 执行状态
- 执行耗时

Tool Call 应支持回放和审计。

---

# 11. Runtime Memory

Context Session 可以维护临时运行记忆。

例如：

```text
Working Memory

Recent Thoughts

Intermediate Result

Temporary Variables
```

Runtime Memory 生命周期不得超过当前 Session。

不得直接替代 Knowledge Object。

---

# 12. Session Completion

Session 完成后：

可以：

- 保存 Decision；
- 保存 Evidence；
- 保存 Task；
- 保存 Summary。

不能：

直接保存 Prompt。

Prompt 属于运行过程。

---

# 13. Design Principles

Context Session 应遵循以下原则。

## Runtime First

Context Session 是运行时对象。

不是知识对象。

---

## Context Is Dynamic

Context 应按需构建。

不得长期保存。

---

## Traceable

所有运行过程应可追溯。

---

## AI Native

Context Session 应支持：

- LLM
- Agent
- Workflow
- Tool Calling

---

## Technology Independent

Context Session 不绑定：

- LangGraph
- LangChain
- AutoGen
- CrewAI
- MCP

仅定义运行模型。

---

# 14. Out of Scope

本文档不涉及：

- Prompt 模板
- Workflow 编排
- Agent 实现
- MCP 协议
- Tool API
- 向量数据库

将在后续规范中定义。

---

# 15. References

- 001 Domain Overview
- 002 Domain Object Model
- 003 Common Object Specification
- 004 Relationship Model
- 005 Knowledge Object Model

---

# 修订记录

| 版本 | 日期 | 内容 |
|------|------|------|
| v0.1.0 | 2026-07-29 | 初始版本 |