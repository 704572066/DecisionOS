# 001 领域总览（Domain Overview）

> **文档编号：** 001  
> **分类：** Domain Specification  
> **状态：** Draft  
> **版本：** v0.1.0  
> **最后更新：** 2026-07-29

---

# 1. 文档目的

本文档定义 DecisionOS 的业务领域模型（Domain Model），描述平台中的核心业务对象及其关系。

本文档回答的问题：

> **DecisionOS 的业务世界由哪些领域组成？**

本文档作为所有领域规范（Specs）的基础。

---

# 2. 领域设计目标

DecisionOS 的领域模型遵循以下目标：

- 统一业务语言（Ubiquitous Language）
- 明确对象边界
- 面向业务，而非数据库
- 支持 AI 理解
- 支持知识关联
- 支持上下文构建

---

# 3. 核心领域

DecisionOS 的业务世界由以下领域组成：

- Organization（组织）
- Person（人员）
- Customer（客户）
- Project（项目）
- Meeting（会议）
- Decision（决策）
- Task（任务）
- Document（文档）
- Evidence（证据）
- Context（上下文）

---

# 4. 领域关系

```text
Organization
        │
        ▼
Project
        │
        ▼
Meeting
        │
        ▼
Decision
        │
        ▼
Task
```

Document、Person、Customer、Evidence 在整个过程中提供关联和支撑。

---

# 5. 领域对象说明

## Organization

企业组织。

拥有项目、成员和资源。

---

## Person

参与者。

可以参与会议、负责任务、做出决策。

---

## Project

承载业务目标。

项目产生会议、任务和决策。

---

## Meeting

讨论与沟通的载体。

会议可能形成决策。

---

## Decision

业务决策结果。

Decision 是 DecisionOS 最重要的业务对象之一。

---

## Task

决策落地后的执行单元。

---

## Document

知识载体。

包括文档、图片、附件等。

---

## Evidence

支撑决策的依据。

Evidence 可以来自：

- Meeting
- Document
- Task
- Project
- 外部系统

---

## Context

运行时聚合对象。

Context 不是长期保存的业务对象。

Context 用于 AI 推理和决策支持。

---

# 6. 领域原则

DecisionOS 遵循以下原则：

- Facts First（事实优先）
- Context Driven（上下文驱动）
- Evidence Based（证据支撑）
- Human Decision（人类决策）
- Continuous Knowledge（知识持续积累）

---

# 7. 不在本文档讨论范围

本文档不涉及：

- 字段定义
- JSON Schema
- API
- 数据库
- 生命周期细节

这些内容将在各对象规范中定义。

---

# 8. 后续领域规范

后续将分别定义：

- 002_Knowledge_Model.md
- 003_Context_Session.md
- 004_Meeting.md
- 005_Decision.md
- 006_Evidence.md
- 007_Project.md
- 008_Task.md
- 009_Document.md

---

# 修订记录

| 版本 | 日期 | 内容 |
|------|------|------|
| v0.1.0 | 2026-07-29 | 初始版本 |