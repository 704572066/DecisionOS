# 010 Evidence Specification

> **文档编号：** 010
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

本文档定义 DecisionOS 中 Evidence 的统一业务规范。

Evidence 是企业业务中的可验证事实（Verifiable Fact），用于支持或反驳业务结论、分析结果和决策。

Evidence 是企业知识网络的重要组成部分，也是 AI 推理和企业决策的重要依据。

本文档定义：

- Evidence 的业务语义；
- Evidence 的组成结构；
- 生命周期；
- 与其他知识对象的关系；
- AI 在 Evidence 生命周期中的角色；
- 治理原则。

---

# 2. 定义

Evidence 是能够支持或反驳某项业务结论的可验证事实。

Evidence 应具备以下特征：

- 来源明确；
- 内容可验证；
- 可被引用；
- 可建立关系；
- 可持续治理。

Evidence 不是：

- 文件；
- 图片；
- PDF；
- 邮件；
- Prompt；
- AI 输出。

这些对象可以作为 Evidence 的来源或载体，但不是 Evidence 本身。

---

# 3. 设计目标

Evidence 应满足以下目标：

- 建立企业事实层；
- 支持 AI 推理；
- 支持决策追溯；
- 支持知识治理；
- 支持多来源融合；
- 支持长期复用。

---

# 4. Evidence 基本结构

Evidence 应至少包含以下信息：

| 属性 | 说明 |
|------|------|
| Evidence ID | 唯一标识 |
| Title | 标题 |
| Fact Statement | 事实描述 |
| Source | 来源 |
| Status | 当前状态 |
| Created Time | 创建时间 |
| Verified Time | 验证时间（如适用） |

Evidence 继承 Knowledge Object 的公共能力。

---

# 5. Carrier 与 Evidence

DecisionOS 区分 Evidence 与 Carrier。

Carrier 是事实的载体。

Evidence 是经过识别和组织后的业务事实。

典型关系如下：

```text
Carrier
    │
contains
    ▼
Evidence
```

Carrier 可以包括：

- Meeting Transcript
- Meeting Recording
- Document
- Email
- ERP Record
- CRM Record
- Wiki
- API Response

一个 Carrier 可以包含多个 Evidence。

一个 Evidence 也可以来源于多个 Carrier。

---

# 6. 生命周期

Evidence 建议采用以下生命周期：

```text
Collected
    │
Verified
    │
Accepted
    │
Referenced
    │
Archived
```

可扩展状态：

```text
Rejected
```

说明：

- **Collected**：已采集。
- **Verified**：已验证。
- **Accepted**：被确认可作为业务事实。
- **Referenced**：已被其他对象引用。
- **Archived**：归档保存。
- **Rejected**：确认无效或错误，不作为业务依据。

Evidence 不应因错误而直接删除，应保留历史状态。

---

# 7. Relationship

Evidence 可以建立以下关系：

| Relationship | Target |
|--------------|--------|
| extracted_from | Document |
| extracted_from | Meeting |
| extracted_from | Email |
| supports | Decision |
| contradicts | Decision |
| belongs_to | Project |
| references | Evidence |
| related_to | Task |

Evidence 是知识网络中的桥梁对象。

---

# 8. Evidence Strength

Evidence 可以包含质量属性。

建议包括：

| 属性 | 说明 |
|------|------|
| Strength | 证据强度 |
| Confidence | 可信度 |
| Verification Status | 验证状态 |
| Source Reliability | 来源可靠性 |
| Freshness | 时效性 |

Strength 建议采用：

- Weak
- Medium
- Strong
- Verified

这些属性可辅助 AI 进行证据评估和决策分析。

---

# 9. AI 能力

AI 可以参与 Evidence 生命周期。

例如：

- 从 Carrier 中抽取事实；
- 去重与归并；
- 建立 Relationship；
- 判断相关性；
- 辅助验证；
- 评估可信度；
- 推荐支持或反驳关系。

AI 可以辅助处理 Evidence，但不自动决定其真实性。

Evidence 的最终确认应遵循企业治理规则。

---

# 10. Knowledge Contribution

Evidence 是连接知识与决策的重要桥梁。

典型演进过程如下：

```text
Carrier
      │
contains
      ▼
Evidence
      │
supports
      ▼
Decision
      │
creates
      ▼
Task
```

Evidence 将原始业务信息转化为可复用的事实资产。

---

# 11. Explainability

Evidence 应支持完整追溯。

每项 Evidence 应能够回答：

- 来源于哪个 Carrier？
- 是否经过验证？
- 支持或反驳哪些 Decision？
- 被哪些 Task 引用？
- 是否存在其他关联 Evidence？

Explainability 是企业级 AI 的关键能力。

---

# 12. Governance

Evidence 应支持统一治理。

包括：

- 权限控制；
- 生命周期管理；
- 分类管理；
- 标签管理；
- 审计；
- 保留策略；
- 版本管理。

Evidence 属于企业知识资产。

---

# 13. Object Responsibilities

## Evidence 负责

- 保存业务事实；
- 保存事实来源；
- 保存验证状态；
- 保存可信度；
- 建立事实关系；
- 支持 AI 推理；
- 支持知识追溯。

## Evidence 不负责

- 保存原始文件（Document）。
- 保存完整会议内容（Meeting）。
- 保存正式业务决策（Decision）。
- 保存运行时上下文（Context）。
- 保存工具调用过程（Tool Call）。

---

# 14. Design Principles

Evidence 应遵循以下原则。

## Fact First

Evidence 表达业务事实，而不是数据载体。

---

## Verifiable

Evidence 应具有可验证来源。

---

## Relationship First

Evidence 应通过 Relationship 与其他对象建立联系。

---

## Explainable

Evidence 应支持完整追溯和解释。

---

## Technology Independent

Evidence 属于逻辑模型。

不得绑定：

- OCR 引擎；
- ASR 引擎；
- NLP 模型；
- 向量数据库；
- AI 框架。

---

# 15. Out of Scope

本文档不涉及：

- OCR 实现；
- ASR 实现；
- 信息抽取算法；
- RAG 检索；
- Prompt Engineering；
- Schema 定义；
- 数据库存储。

将在后续规范中说明。

---

# 16. References

- 001 Domain Overview
- 002 Domain Object Model
- 003 Common Object Specification
- 004 Relationship Model
- 005 Knowledge Object Model
- 006 Context Session Specification
- 007 Context Specification
- 008 Meeting Specification
- 009 Decision Specification

---

# 修订记录

| 版本 | 日期 | 内容 |
|------|------|------|
| v0.1.0 | 2026-07-31 | 初始版本 |