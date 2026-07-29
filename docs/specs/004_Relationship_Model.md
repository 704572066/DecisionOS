# 004 Relationship Model

> **文档编号：** 004
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

本文档定义 DecisionOS 的统一关系模型（Relationship Model）。

Relationship 用于描述领域对象之间的业务联系。

Relationship 是 Knowledge Graph、Context Engine、RAG 检索以及 AI 推理的重要组成部分。

本文档回答以下问题：

- Relationship 是什么？
- 哪些对象可以建立 Relationship？
- Relationship 有哪些类型？
- Relationship 如何参与 Context 构建？
- Relationship 如何支持 AI 推理？

---

# 2. 设计目标

Relationship Model 应满足以下目标：

- Business Oriented（面向业务）
- Graph Friendly（适配图模型）
- AI Native（AI 原生）
- Traceable（可追溯）
- Extensible（可扩展）
- Technology Independent（技术无关）

---

# 3. Relationship 定义

Relationship 表示两个 Domain Object 之间的业务关联。

Relationship 自身也是一种领域对象。

Relationship 不属于某个对象，而是连接对象。

例如：

```text
Meeting
      │
      └──── produces ─────► Decision
```

Relationship 应能够独立表达业务语义。

---

# 4. Relationship 基本结构

每个 Relationship 至少应包含：

| 字段 | 说明 |
|------|------|
| id | 唯一标识 |
| source | 源对象 |
| target | 目标对象 |
| relationType | 关系类型 |
| direction | 方向 |
| createdAt | 创建时间 |
| metadata | 扩展属性 |

Relationship 应具有唯一身份。

---

# 5. Relationship 分类

DecisionOS 将 Relationship 分为四类。

## 5.1 Structural Relationship

长期存在的业务关系。

例如：

- Project contains Meeting
- Meeting produces Decision
- Decision creates Task
- Document belongs_to Project

特点：

- 长期保存
- 属于 Knowledge Graph
- 可持续演化

---

## 5.2 Reference Relationship

表示引用关系。

例如：

- Decision references Document
- Meeting references Repository
- Evidence references URL

特点：

- 不拥有数据
- 保存引用
- 支持同步更新

---

## 5.3 Runtime Relationship

运行期间动态建立。

例如：

Context：

```text
Context
    ├── uses ─────► Meeting
    ├── analyzes ─► Decision
    ├── retrieves ─► Evidence
```

特点：

- 生命周期短
- 不长期保存
- 可重新构建

---

## 5.4 Derived Relationship

推理过程中自动生成。

例如：

AI：

```text
Customer
       │
       └──── impacts ───► Decision
```

该关系来自推理，而不是业务系统。

Derived Relationship 应具有可信度（Confidence）。

---

# 6. Relationship 生命周期

Relationship 生命周期：

```text
Create
     │
Active
     │
Updated
     │
Archived
```

Runtime Relationship：

```text
Create
     │
Use
     │
Destroy
```

---

# 7. 常见关系类型

建议采用统一命名。

| 类型 | 说明 |
|------|------|
| contains | 包含 |
| belongs_to | 属于 |
| references | 引用 |
| produces | 产生 |
| creates | 创建 |
| owns | 拥有 |
| assigned_to | 分配 |
| attends | 参与 |
| supported_by | 支撑 |
| depends_on | 依赖 |
| impacts | 影响 |
| related_to | 关联 |

Relation Type 应保持稳定。

---

# 8. Knowledge Graph

Knowledge Graph 由：

- Domain Object
- Relationship

共同组成。

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

Knowledge Graph 是企业知识网络。

---

# 9. Context Relationship

Context 不复制 Relationship。

Context 引用已有 Relationship。

例如：

```text
Meeting
        │
Decision
        │
Task

↓

Context

↓

Meeting
Decision
Task
Relationship
```

Context 应保持轻量。

---

# 10. AI 推理中的 Relationship

AI 应优先利用 Relationship，而不是孤立对象。

例如：

Decision：

```
Decision A
```

意义有限。

如果结合：

```text
Meeting
        │
produces
        │
Decision
        │
supported_by
        │
Evidence
        │
creates
        │
Task
```

AI 可以理解完整业务链路。

Relationship 是构建上下文的重要组成部分。

---

# 11. 设计原则

Relationship 应遵循：

## 业务语义

Relationship 必须表达明确业务意义。

避免：

```
Link
```

推荐：

```
produces
contains
references
```

---

## 可追溯

Relationship 应能够追溯来源。

例如：

- 用户创建
- 系统同步
- AI 推理

---

## 可扩展

Relationship 支持：

- metadata
- confidence
- weight
- tags

---

## 可版本化

Knowledge Relationship 建议支持版本。

---

## 技术无关

Relationship Model 不绑定：

- Neo4j
- PostgreSQL
- Elasticsearch

仅定义逻辑模型。

---

# 12. 不在本文档讨论范围

本文档不涉及：

- 图数据库设计
- Graph API
- Cypher 查询
- SQL 表结构
- ORM
- GraphQL

将在后续文档说明。

---

# 13. 后续规范

下一阶段建议进入：

- 005_Knowledge_Model.md
- 006_Context_Session.md
- 007_Meeting.md
- 008_Decision.md
- 009_Evidence.md
- 010_Project.md
- 011_Task.md
- 012_Document.md

---

# 修订记录

| 版本 | 日期 | 内容 |
|------|------|------|
| v0.1.0 | 2026-07-29 | 初始版本 |