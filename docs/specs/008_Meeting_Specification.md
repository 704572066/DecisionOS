# 008 Meeting Specification

> **文档编号：** 008
>
> **分类：** Domain Specification
>
> **状态：** Draft
>
> **版本：** v0.1.0
>
> **最后更新：** 2026-07-30

---

# 1. 文档目的

本文档定义 DecisionOS 中 Meeting 的统一业务规范。

Meeting 是企业协作过程中产生业务知识的重要来源。

Meeting 用于记录一次具有明确业务目标的协作活动，并作为 Decision、Task、Evidence 等知识对象的重要来源。

本文档定义：

- Meeting 的业务语义；
- Meeting 的组成结构；
- 生命周期；
- 与其他知识对象的关系；
- 治理原则。

---

# 2. 定义

Meeting 是一次围绕明确业务目标开展的协作事件（Collaboration Event）。

Meeting 可以来自：

- 线下会议
- 视频会议
- 电话会议
- 客户拜访
- 项目评审
- 技术评审
- 售前沟通
- 事故复盘
- 工作坊
- 其他正式业务沟通

Meeting 的核心价值不是保存会议记录，而是沉淀企业知识。

---

# 3. 设计目标

Meeting 应满足以下目标：

- 记录协作过程；
- 保留业务上下文；
- 支持 AI 理解；
- 支持知识沉淀；
- 支持长期治理；
- 支持业务追溯。

---

# 4. Meeting 基本结构

Meeting 应至少包含以下信息：

| 属性 | 说明 |
|------|------|
| Meeting ID | 唯一标识 |
| Title | 标题 |
| Objective | 业务目标 |
| Organizer | 发起人 |
| Participants | 参与者 |
| Start Time | 开始时间 |
| End Time | 结束时间 |
| Status | 当前状态 |

Meeting 继承 Knowledge Object 的公共能力。

---

# 5. Meeting 内容

Meeting 可以包含：

- Agenda（议程）
- Transcript（转写）
- Summary（总结）
- Discussion（讨论）
- Attachments（附件）
- Decisions（决策）
- Tasks（任务）
- Evidence（证据）

Meeting 本身不要求所有内容必须存在。

---

# 6. 生命周期

Meeting 建议采用以下生命周期：

```text
Planned
    │
In Progress
    │
Completed
    │
Archived
```

必要时可扩展：

```text
Cancelled
```

Completed 后通常进入知识治理流程。

---

# 7. Relationship

Meeting 可以建立以下关系：

| Relationship | Target |
|--------------|--------|
| produces | Decision |
| creates | Task |
| supported_by | Evidence |
| belongs_to | Project |
| references | Document |
| attends | Person |
| organized_by | Person |

Meeting 是知识网络中的重要节点。

---

# 8. Knowledge Production

Meeting 是企业知识的重要来源。

典型过程：

```text
Meeting
      │
      ▼
Discussion
      │
      ▼
Decision
      │
      ▼
Task
      │
      ▼
Evidence
```

Meeting 可以产生多个新的 Knowledge Object。

---

# 9. AI 能力

Meeting 应支持：

- 自动摘要；
- 决策提取；
- Action Item 提取；
- 风险识别；
- 主题聚类；
- 待办生成；
- 证据关联；
- 历史会议关联。

AI 输出应保持可追溯。

---

# 10. Explainability

Meeting 应支持解释。

例如：

某项 Decision 应能够回答：

- 来源于哪次 Meeting？
- 哪些人员参与讨论？
- 哪些 Evidence 支撑？
- 是否形成了 Task？

Meeting 应成为知识追溯的重要入口。

---

# 11. Governance

Meeting 应支持：

- 权限控制；
- 生命周期管理；
- 分类管理；
- 标签管理；
- 审计；
- 保留策略。

Meeting 属于企业知识资产。

---

# 12. Design Principles

Meeting 应遵循以下原则。

## Business First

Meeting 描述业务协作，而不是音视频文件。

---

## Knowledge First

Meeting 的目标是沉淀知识。

---

## Relationship First

Meeting 应通过 Relationship 与其他对象建立联系。

---

## Traceable

Meeting 应支持完整追溯。

---

## Technology Independent

Meeting 属于逻辑模型。

不得绑定：

- Zoom
- Teams
- 飞书
- 钉钉
- 腾讯会议

这些属于数据来源，而不是业务模型。

---

# 13. Out of Scope

本文档不涉及：

- 音视频采集；
- ASR；
- OCR；
- NLP；
- AI Prompt；
- 数据库存储。

将在后续规范中定义。

---

# 14. References

- 001 Domain Overview
- 002 Domain Object Model
- 003 Common Object Specification
- 004 Relationship Model
- 005 Knowledge Object Model
- 006 Context Session Specification
- 007 Context Specification

---

# 修订记录

| 版本 | 日期 | 内容 |
|------|------|------|
| v0.1.0 | 2026-07-30 | 初始版本 |