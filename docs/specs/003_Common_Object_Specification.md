# 003 通用对象规范（Common Object Specification）

> **文档编号：** 003
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

本文档定义 DecisionOS 所有 Domain Object 的统一规范。

所有领域对象 MUST 遵循本文档定义的公共约束。

本文档不定义具体业务对象，而定义对象的公共属性、生命周期和设计原则。

---

# 2. 适用范围

本规范适用于：

- Meeting
- Decision
- Project
- Task
- Document
- Evidence
- Person
- Organization
- Customer

以及未来新增的 Knowledge Object。

---

# 3. 基础属性

所有 Domain Object 应至少具备以下基础属性。

| 属性 | 必选 | 说明 |
|------|------|------|
| id | MUST | 全局唯一标识 |
| type | MUST | 对象类型 |
| name | SHOULD | 可读名称 |
| description | MAY | 描述信息 |
| owner | SHOULD | 所有者 |
| status | SHOULD | 当前状态 |
| version | MUST | 对象版本 |
| createdAt | MUST | 创建时间 |
| updatedAt | MUST | 更新时间 |
| labels | MAY | 标签集合 |
| metadata | MAY | 扩展元数据 |

---

# 4. Identity

每个对象必须具有唯一身份。

要求：

- 全局唯一
- 不可修改
- 生命周期内保持稳定

推荐使用 UUID 或 ULID。

---

# 5. Version

Knowledge Object 应支持版本管理。

原则：

- 新版本不覆盖历史版本。
- 保留审计记录。
- 支持版本回溯。

---

# 6. Relationship

对象之间通过 Relationship 建立关联。

关系应具有：

- source
- target
- relationType

例如：

- Meeting → Decision
- Decision → Task
- Project → Meeting
- Evidence → Decision

Relationship 应支持扩展。

---

# 7. Metadata

Metadata 用于保存扩展属性。

要求：

- 不影响核心模型。
- 支持不同业务场景扩展。
- 不得替代核心字段。

---

# 8. 生命周期

Knowledge Object 建议采用统一生命周期：

```text
Draft
   │
Active
   │
Archived
   │
Deleted
```

不同对象可扩展状态，但不应破坏基本生命周期。

---

# 9. 设计原则

所有对象应遵循：

- Single Responsibility（单一职责）
- Stable Identity（身份稳定）
- Immutable History（历史不可篡改）
- Extensible Metadata（元数据可扩展）
- Traceable Relationship（关系可追溯）

---

# 10. 不在本文档讨论范围

本文档不涉及：

- JSON Schema
- OpenAPI
- 数据库存储
- ORM
- 编程语言实现

这些内容将在后续规范中定义。

---

# 11. 后续规范

本文档之后将进入具体领域对象：

- 004_Knowledge_Model.md
- 005_Context_Session.md
- 006_Meeting.md
- 007_Decision.md
- 008_Evidence.md
- 009_Project.md
- 010_Task.md
- 011_Document.md

---

# 修订记录

| 版本 | 日期 | 内容 |
|------|------|------|
| v0.1.0 | 2026-07-29 | 初始版本 |