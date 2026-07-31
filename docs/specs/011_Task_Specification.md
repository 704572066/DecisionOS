# 011 Task Specification

> **文档编号：** 011
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

本文档定义 DecisionOS 中 Task 的统一业务规范。

Task 是企业为落实一个或多个 Decision 而执行的业务行动（Business Action）。

Task 连接企业决策与业务执行，是 DecisionOS 知识闭环中的执行层对象。

本文档定义：

- Task 的业务语义；
- Task 的组成结构；
- 生命周期；
- 与其他知识对象的关系；
- AI 在 Task 生命周期中的角色；
- 治理原则。

---

# 2. 定义

Task 是为了达成明确业务目标而执行的业务行动。

Task 应具备以下特征：

- 来源明确；
- 目标明确；
- 责任明确；
- 可执行；
- 可跟踪；
- 可评估。

Task 不等同于：

- Todo；
- 工单；
- 聊天消息；
- AI 输出；
- Prompt。

Task 是正式的 Knowledge Object。

---

# 3. 设计目标

Task 应满足以下目标：

- 落实业务决策；
- 推动业务执行；
- 支持执行追踪；
- 形成执行反馈；
- 支持 AI 辅助执行；
- 支持持续治理。

---

# 4. Task 基本结构

Task 应至少包含以下信息：

| 属性 | 说明 |
|------|------|
| Task ID | 唯一标识 |
| Title | 标题 |
| Objective | 业务目标 |
| Owner | 责任主体 |
| Assignee | 执行人 |
| Priority | 优先级 |
| Status | 当前状态 |
| Deadline | 截止时间 |
| Result | 执行结果 |

Task 继承 Knowledge Object 的公共能力。

---

# 5. Task Execution

Task 应围绕业务目标组织。

建议包含：

```text
Task
│
├── Objective
├── Execution Plan
├── Owner
├── Assignee
├── Priority
├── Deadline
├── Status
├── Progress
├── Result
├── Related Decision
├── Related Evidence
└── Trace
```

其中：

- **Objective**：业务目标。
- **Execution Plan**：执行计划。
- **Progress**：执行进度。
- **Result**：执行结果。
- **Related Decision**：来源 Decision。
- **Related Evidence**：执行产生的 Evidence。
- **Trace**：执行过程追溯。

---

# 6. 生命周期

Task 建议采用以下生命周期：

```text
Planned
    │
Assigned
    │
In Progress
    │
Completed
```

可扩展状态：

```text
Blocked
Failed
Cancelled
```

说明：

- **Blocked**：执行受阻。
- **Failed**：执行失败。
- **Cancelled**：取消执行。

Task 应保留完整生命周期历史。

---

# 7. Relationship

Task 可以建立以下关系：

| Relationship | Target |
|--------------|--------|
| created_by | Decision |
| belongs_to | Project |
| assigned_to | Person |
| produces | Evidence |
| references | Document |
| related_to | Task |

Task 是连接决策与执行的重要节点。

---

# 8. Outcome Driven

Task 应以业务结果为导向，而不是动作本身。

例如：

错误：

```text
打电话
```

正确：

```text
完成客户付款确认
```

业务目标比执行动作更重要。

---

# 9. AI 能力

AI 可以参与 Task 生命周期。

例如：

- 自动拆分复杂 Task；
- 推荐负责人；
- 推荐截止时间；
- 风险预测；
- 自动提醒；
- 自动生成执行计划；
- 自动生成执行总结；
- 自动检查执行状态。

AI 可以辅助执行。

AI 不自动完成业务责任。

Task 的最终状态应由责任主体确认。

---

# 10. Knowledge Contribution

Task 是企业知识持续演进的重要组成部分。

典型流程如下：

```text
Decision
      │
creates
      ▼
Task
      │
Execution
      ▼
Evidence
      │
supports
      ▼
Next Decision
```

Task 不仅执行业务，也产生新的业务知识。

---

# 11. Explainability

Task 应支持完整追溯。

每项 Task 应能够回答：

- 来源于哪个 Decision？
- 为什么创建？
- 谁负责？
- 当前执行状态？
- 产生了哪些 Evidence？
- 是否达成业务目标？

Explainability 是企业执行治理的重要能力。

---

# 12. Governance

Task 应支持统一治理。

包括：

- 权限控制；
- 生命周期管理；
- 分类管理；
- 标签管理；
- 审计；
- 保留策略；
- 版本管理。

Task 属于企业执行知识资产。

---

# 13. Object Responsibilities

## Task 负责

- 落实业务 Decision；
- 保存业务目标；
- 保存执行状态；
- 保存执行结果；
- 建立执行 Relationship；
- 产生新的 Evidence；
- 支持业务追溯。

## Task 不负责

- 保存正式 Decision。
- 保存完整 Meeting。
- 保存 Carrier。
- 保存 Runtime Context。
- 保存 Tool Call。

---

# 14. Object Relationship

Task 在企业知识网络中的位置如下：

```text
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
      │
supports
      ▼
Decision
```

Task 是企业决策闭环的重要执行节点。

---

# 15. Design Principles

Task 应遵循以下原则。

## Outcome Driven

以业务目标为中心，而不是执行动作。

---

## Decision Driven

Task 应来源于明确业务 Decision。

---

## Traceable

Task 应支持完整执行追溯。

---

## Relationship First

Task 应通过 Relationship 与其他对象建立联系。

---

## Technology Independent

Task 属于逻辑模型。

不得绑定：

- 项目管理软件；
- 工作流引擎；
- 工单系统；
- OA 系统；
- AI 框架。

---

# 16. Out of Scope

本文档不涉及：

- 工作流实现；
- 甘特图；
- 通知机制；
- 自动调度；
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

---

# 修订记录

| 版本 | 日期 | 内容 |
|------|------|------|
| v0.1.0 | 2026-07-31 | 初始版本 |