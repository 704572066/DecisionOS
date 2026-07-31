# 012 Project Specification

> **文档编号：** 012
>
> **分类：** Domain Specification
>
> **状态：** Draft
>
> **版本：** v0.1.0
>
> **最后更新：** 2026-07-31

---

# 1. 文档目的

本文档定义 DecisionOS 中 Project 的统一业务规范。

Project 是围绕持续业务目标组织的一组 Knowledge Object 的业务边界（Business Boundary）。

Project 为企业知识提供统一的组织、治理、权限和生命周期管理能力，是 DecisionOS 企业知识网络中的聚合根（Aggregate Root）。

本文档定义：

- Project 的业务语义；
- Project 的组成结构；
- 生命周期；
- 与其他知识对象的关系；
- AI 在 Project 中的角色；
- 治理原则。

---

# 2. 定义

Project 是围绕某一持续业务目标建立的业务知识边界。

Project 可以包含多个 Knowledge Object，例如：

- Meeting
- Decision
- Task
- Evidence
- Document
- Person
- Organization

Project 的职责是组织知识，而不是保存知识内容。

Project 不等同于：

- 文件夹；
- 项目管理工具中的项目；
- 任务集合；
- 数据库分区。

Project 是企业知识图谱中的聚合根。

---

# 3. 设计目标

Project 应满足以下目标：

- 定义业务边界；
- 聚合知识对象；
- 建立统一上下文；
- 支持 AI 检索；
- 支持统一治理；
- 支持跨对象协作。

---

# 4. Project 基本结构

Project 应至少包含以下信息：

| 属性 | 说明 |
|------|------|
| Project ID | 唯一标识 |
| Name | 名称 |
| Business Goal | 业务目标 |
| Owner | 项目负责人 |
| Status | 当前状态 |
| Start Time | 开始时间 |
| End Time | 结束时间（如适用） |

Project 继承 Knowledge Object 的公共能力。

---

# 5. Project Composition

Project 可以聚合多个 Knowledge Object。

典型组成如下：

```text
Project
│
├── Meeting
├── Decision
├── Task
├── Evidence
├── Document
├── Person
└── Organization
```

Project 聚合对象，但不复制对象内容。

Knowledge Object 可以通过 Relationship 与 Project 建立关联。

---

# 6. 生命周期

Project 建议采用以下生命周期：

```text
Initiated
    │
Planning
    │
Active
    │
Completed
    │
Archived
```

可扩展状态：

```text
Suspended
Cancelled
```

Project 生命周期通常长于其包含的大多数对象。

---

# 7. Relationship

Project 可以建立以下关系：

| Relationship | Target |
|--------------|--------|
| contains | Meeting |
| contains | Decision |
| contains | Task |
| contains | Evidence |
| contains | Document |
| has_member | Person |
| belongs_to | Organization |
| depends_on | Project |
| related_to | Project |

Project 是知识网络中的组织边界，而不是业务内容本身。

---

# 8. Business Boundary

Project 定义企业知识的业务边界。

典型结构如下：

```text
Organization
      │
owns
      ▼
Project
      │
contains
      ▼
Knowledge Graph
```

所有 Context、Decision 和 AI 推理均应优先在业务边界内进行。

跨 Project 检索应遵循权限和治理策略。

---

# 9. AI 能力

AI 可以参与 Project 生命周期。

例如：

- 自动构建项目 Context；
- 聚合相关 Knowledge Object；
- 自动生成项目摘要；
- 分析项目风险；
- 推荐相关 Evidence；
- 推荐相关 Decision；
- 生成项目周报；
- 分析项目健康度。

AI 辅助知识组织和分析。

AI 不替代业务管理职责。

---

# 10. Knowledge Contribution

Project 是企业知识的重要组织单元。

典型结构如下：

```text
Project
      │
contains
      ▼
Meeting
      │
produces
      ▼
Decision
      │
creates
      ▼
Task
      │
produces
      ▼
Evidence
```

Project 为企业知识提供统一边界，而不是业务内容。

---

# 11. Explainability

Project 应支持完整追溯。

每个 Project 应能够回答：

- 包含哪些 Meeting？
- 形成了哪些 Decision？
- 当前有哪些 Task？
- 累积了哪些 Evidence？
- 引用了哪些 Document？
- 当前业务目标是什么？

Project 是企业知识导航的重要入口。

---

# 12. Governance

Project 应支持统一治理。

包括：

- 权限控制；
- 生命周期管理；
- 分类管理；
- 标签管理；
- 审计；
- 保留策略；
- 成员管理。

Project 是企业知识治理的重要边界。

---

# 13. Object Responsibilities

## Project 负责

- 定义业务边界；
- 聚合 Knowledge Object；
- 管理生命周期；
- 管理权限；
- 提供统一 Context；
- 支持 AI 检索；
- 支持企业治理。

## Project 不负责

- 保存 Meeting 内容。
- 保存 Decision 内容。
- 保存 Evidence 内容。
- 保存 Task 内容。
- 保存 Document 内容。
- 保存 Runtime Context。

---

# 14. Object Relationship

Project 在企业知识网络中的位置如下：

```text
Organization
      │
owns
      ▼
Project
      │
contains
      ▼
Meeting
      │
produces
      ▼
Decision
      │
creates
      ▼
Task
      │
produces
      ▼
Evidence
```

Project 是知识网络的组织边界。

---

# 15. Design Principles

Project 应遵循以下原则。

## Business Boundary First

Project 定义业务边界，而不是任务集合。

---

## Aggregate Root

Project 聚合知识对象，不复制业务内容。

---

## Context Oriented

Project 为 Context Engine 提供统一的业务范围。

---

## Governance First

Project 是权限、治理和生命周期管理的基础。

---

## Technology Independent

Project 属于逻辑模型。

不得绑定：

- Jira；
- GitHub Projects；
- Trello；
- Asana；
- Microsoft Project；
- AI 框架。

---

# 16. Out of Scope

本文档不涉及：

- 项目管理方法论（Scrum、Kanban 等）；
- 甘特图；
- 资源调度；
- 成本管理；
- Prompt Engineering；
- Schema 定义；
- 数据库存储。

将在后续规范中说明。

---

# 17. References

- 001 Domain Overview
- 002 Domain Object Model
- 003 Common Object Specification
- 004 Relationship Model
- 005 Knowledge Object Model
- 006 Context Session Specification
- 007 Context Specification
- 008 Meeting Specification
- 009 Decision Specification
- 010 Evidence Specification
- 011 Task Specification

---

# 修订记录

| 版本 | 日期 | 内容 |
|------|------|------|
| v0.1.0 | 2026-07-31 | 初始版本 |