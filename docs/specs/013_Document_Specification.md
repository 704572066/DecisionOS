# 013 Document Specification

> **文档编号：** 013
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

本文档定义 DecisionOS 中 Document 的统一业务规范。

Document 是承载业务信息的知识载体（Knowledge Carrier）。

Document 为企业知识提供统一的组织、引用、版本和治理能力，是 Evidence 的主要来源之一。

本文档定义：

- Document 的业务语义；
- Document 的组成结构；
- 生命周期；
- 与其他知识对象的关系；
- AI 在 Document 生命周期中的角色；
- 治理原则。

---

# 2. 定义

Document 是能够承载业务信息并参与知识治理的业务对象。

Document 可以来源于：

- 会议纪要；
- 合同；
- 方案；
- 报告；
- 邮件；
- Wiki 页面；
- API 返回内容；
- ERP 导出记录；
- CRM 导出记录。

Document 不等同于：

- 文件（File）；
- PDF；
- Word；
- 图片；
- 音频；
- 视频。

这些属于物理或数字载体，而不是业务对象。

Document 继承 Knowledge Object 的公共能力。

---

# 3. 设计目标

Document 应满足以下目标：

- 承载业务信息；
- 支持知识抽取；
- 支持版本管理；
- 支持统一引用；
- 支持 AI 理解；
- 支持长期治理。

---

# 4. Document 基本结构

Document 应至少包含以下信息：

| 属性 | 说明 |
|------|------|
| Document ID | 唯一标识 |
| Title | 标题 |
| Type | 文档类型 |
| Author | 作者 |
| Status | 当前状态 |
| Version | 当前版本 |
| Created Time | 创建时间 |
| Updated Time | 更新时间 |

---

# 5. Document Composition

Document 可以包含多个组成部分。

建议结构如下：

```text
Document
│
├── Metadata
├── Sections
├── References
├── Attachments
├── Evidence
├── Version
└── Trace
```

说明：

- **Metadata**：基础元数据。
- **Sections**：文档内容结构。
- **References**：引用关系。
- **Attachments**：关联附件。
- **Evidence**：从文档中识别出的业务事实。
- **Version**：版本信息。
- **Trace**：变更历史。

Document 可以包含多个 Evidence。

一个 Evidence 也可以来源于多个 Document。

---

# 6. File 与 Document

DecisionOS 明确区分 File 与 Document。

```text
File
    │
contains
    ▼
Document
    │
contains
    ▼
Evidence
```

其中：

- **File**：物理或数字文件。
- **Document**：业务信息载体。
- **Evidence**：可验证业务事实。

Document 不依赖具体文件格式。

---

# 7. 生命周期

Document 建议采用以下生命周期：

```text
Draft
    │
Published
    │
Revised
    │
Archived
```

可扩展状态：

```text
Deprecated
```

Document 应支持完整版本历史。

---

# 8. Relationship

Document 可以建立以下关系：

| Relationship | Target |
|--------------|--------|
| contains | Evidence |
| generated_by | Meeting |
| supports | Decision |
| belongs_to | Project |
| references | Document |
| attached_to | Task |

Document 是知识网络中的重要载体对象。

---

# 9. AI 能力

AI 可以参与 Document 生命周期。

例如：

- OCR；
- ASR；
- 自动摘要；
- 文档分类；
- 标签生成；
- 实体识别；
- Evidence 抽取；
- Relationship 建立。

AI 可以辅助理解 Document。

AI 不应直接修改原始业务内容。

---

# 10. Knowledge Contribution

Document 是企业知识的重要来源。

典型演进过程如下：

```text
File
      │
contains
      ▼
Document
      │
contains
      ▼
Evidence
      │
supports
      ▼
Decision
```

Document 将原始业务信息组织为可治理知识。

---

# 11. Explainability

Document 应支持完整追溯。

每个 Document 应能够回答：

- 来源于哪个 File？
- 包含哪些 Evidence？
- 支撑哪些 Decision？
- 属于哪个 Project？
- 被哪些对象引用？
- 当前版本是什么？

Explainability 是企业知识治理的重要能力。

---

# 12. Governance

Document 应支持统一治理。

包括：

- 权限控制；
- 生命周期管理；
- 分类管理；
- 标签管理；
- 审计；
- 保留策略；
- 版本管理。

Document 属于企业知识资产。

---

# 13. Object Responsibilities

## Document 负责

- 承载业务信息；
- 管理版本；
- 组织章节；
- 建立引用关系；
- 提供 Evidence 来源；
- 支持 AI 理解；
- 支持知识治理。

## Document 不负责

- 保存正式 Decision。
- 保存 Runtime Context。
- 保存 Tool Call。
- 保存执行状态（Task）。
- 保存业务推理过程。

---

# 14. Object Relationship

Document 在企业知识网络中的位置如下：

```text
Project
      │
contains
      ▼
Document
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

Document 是企业知识的重要载体。

---

# 15. Design Principles

Document 应遵循以下原则。

## Knowledge Carrier First

Document 是业务信息载体，而不是文件格式。

---

## Versionable

Document 应支持完整版本管理。

---

## Relationship First

Document 应通过 Relationship 与其他对象建立联系。

---

## Explainable

Document 应支持知识追溯。

---

## Technology Independent

Document 属于逻辑模型。

不得绑定：

- PDF；
- Word；
- Markdown；
- Notion；
- Confluence；
- OCR 引擎；
- AI 框架。

---

# 16. Out of Scope

本文档不涉及：

- 文件存储；
- 对象存储；
- OCR 实现；
- ASR 实现；
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
- 012 Project Specification

---

# 修订记录

| 版本 | 日期 | 内容 |
|------|------|------|
| v0.1.0 | 2026-07-31 | 初始版本 |