# 002 领域对象模型（Domain Object Model）

> **文档编号：** 002
>
> **分类：** Domain Specification
>
> **状态：** Draft
>
> **版本：** v0.1.0
>
> **最后更新：** 2026-07-29

---

# 1. 文档目的

本文档定义 DecisionOS 的统一领域对象模型（Unified Domain Object Model）。

本文档回答以下问题：

- DecisionOS 中有哪些类型的对象？
- 不同对象承担什么职责？
- 对象之间如何协作？
- 哪些对象可以长期保存？
- 哪些对象仅存在于运行期间？

本文档是所有领域规范（Specification）的基础。

---

# 2. 设计目标

DecisionOS 的领域对象模型遵循以下原则：

- Business First（业务优先）
- Unified Object Model（统一对象模型）
- Runtime Isolation（运行时隔离）
- Knowledge Centric（知识中心）
- Evidence Driven（证据驱动）
- Traceability（可追溯）

---

# 3. Domain Object

DecisionOS 将系统中的所有对象统称为：

> **Domain Object**

任何能够表达业务意义的对象，都属于 Domain Object。

例如：

- Meeting
- Decision
- Project
- Task
- Context
- Evidence
- Person
- Organization

Domain Object 不等同于数据库实体（Entity），也不等同于代码类（Class）。

---

# 4. Domain Object 分类

DecisionOS 将领域对象划分为四类。

```text
                     Domain Object
                           │
     ┌─────────────────────┼─────────────────────┐
     │                     │                     │
Knowledge Object     Runtime Object     Reference Object
     │                     │                     │
Meeting            Context Session      External Source
Decision           Context              Attachment
Project            Prompt               URL
Task               Trace                Repository
Document           AI Response
Person
Organization
Customer
```

每种对象具有不同生命周期和职责。

---

# 5. Knowledge Object

Knowledge Object 是企业长期知识资产。

典型对象：

- Meeting
- Decision
- Project
- Task
- Document
- Person
- Organization
- Customer

特点：

- 长期保存
- 可版本化
- 可检索
- 可引用
- 可建立关联关系

Knowledge Object 构成 DecisionOS 的知识库。

---

# 6. Runtime Object

Runtime Object 仅存在于请求执行期间。

例如：

- Context Session
- Context
- Prompt
- Tool Call
- AI Response
- Trace
- Event

特点：

- 生命周期短
- 默认不持久化
- 面向 AI 推理
- 可根据事实重新构建

Runtime Object 不应作为业务事实来源。

---

# 7. Reference Object

Reference Object 表示外部资源或引用。

例如：

- URL
- Git Repository
- Wiki
- ERP Record
- CRM Record
- External Document
- File Attachment

特点：

- 不拥有数据
- 不复制事实
- 保存引用关系
- 可同步更新

Reference Object 用于连接企业已有系统。

---

# 8. Evidence

Evidence 是一种特殊的领域对象。

Evidence 用于说明：

> 为什么形成这个决策？

Evidence 可以来源于：

- Meeting
- Document
- Email
- Task
- Customer
- 外部系统
- AI 分析结果（可配置）

Evidence 本身不是业务流程，而是业务事实的支撑依据。

一个 Decision 可以关联多个 Evidence。

---

# 9. Context

Context 是 Runtime Object。

Context 不是业务对象。

Context 是：

> 为完成一次推理而动态聚合形成的数据视图。

例如：

```text
Meeting
      │
Decision
      │
Project
      │
Task
      │
Customer
──────────────
      ↓
Business Context
```

Context 可以随时重新构建。

---

# 10. 生命周期

不同对象拥有不同生命周期。

| 类型 | 生命周期 |
|------|----------|
| Knowledge Object | 长期 |
| Runtime Object | 请求期间 |
| Reference Object | 跟随外部系统 |
| Evidence | 长期 |
| Context | 临时 |

---

# 11. 对象关系

```text
                +------------------+
                |  Domain Object   |
                +------------------+
                         │
      ┌──────────────────┼──────────────────┐
      │                  │                  │
      ▼                  ▼                  ▼
Knowledge Object   Runtime Object   Reference Object
      │                  │                  │
      ▼                  ▼                  ▼
Meeting           Context Session      External System
Decision          Context              Repository
Project           Prompt               URL
Task              AI Response          Attachment
Document          Trace
Person
Organization
Customer
      │
      ▼
Evidence
```

---

# 12. 对象设计原则

所有 Domain Object 应遵循以下原则。

## 唯一身份（Identity）

每个对象必须具有唯一标识。

---

## 明确边界（Boundary）

对象职责必须单一。

---

## 可关联（Relationship）

对象之间可以建立引用关系。

---

## 可追溯（Traceability）

对象必须能够追溯其来源。

---

## 可扩展（Extensibility）

对象允许增加元数据，而不破坏已有模型。

---

# 13. 不在本文档讨论范围

本文档不涉及：

- 字段定义
- JSON Schema
- API
- 数据库存储
- ORM
- Java / Go / Python 实现

这些内容将在各对象规范中定义。

---

# 14. 后续规范

本文档之后将继续定义：

- 003_Knowledge_Model.md
- 004_Context_Session.md
- 005_Meeting.md
- 006_Decision.md
- 007_Evidence.md
- 008_Project.md
- 009_Task.md
- 010_Document.md

---

# 修订记录

| 版本 | 日期 | 内容 |
|------|------|------|
| v0.1.0 | 2026-07-29 | 初始版本 |