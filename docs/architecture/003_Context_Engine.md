# Context Engine

Title: Context Engine
Document ID: DOC-003
Version: v0.1
Status: Draft
Owner: Architecture Team
Dependencies:
- DOC-000
- DOC-001
- DOC-002
Last Updated: 2026-07-26

---

# 1. Objective

Context Engine 是 DecisionOS 的核心能力，负责理解当前业务上下文，并从企业知识中检索最相关的历史证据，为决策提供支持。

---

# 2. Responsibilities

- 接收当前会议上下文
- 构建 Context Object
- 检索企业知识
- 排序相关证据
- 输出 Evidence List

---

# 3. Inputs

输入包括：

- ASR 文本流
- 当前会议信息
- 用户身份
- 企业知识库
- 历史会议
- 合同
- 项目
- 客户
- 决策记录

---

# 4. Context Object

建议统一结构：

- meetingTopic
- participants
- customer
- project
- keywords
- intent
- risks
- timeline
- entities

Context Object 是后续所有 AI 能力的统一输入。

---

# 5. Processing Flow

ASR
→ Meeting Understanding
→ Context Object
→ Context Retrieval
→ Evidence Ranking
→ Decision Assistant

---

# 6. Outputs

输出 Evidence List，每条 Evidence 至少包含：

- title
- type
- summary
- source
- relevanceScore
- timestamp

所有 Evidence 必须支持来源追溯。

---

# 7. Performance Requirements

- Context 构建 ≤ 1 秒
- 检索 ≤ 3 秒
- Evidence 返回数量支持配置（默认 Top 5）

---

# 8. Acceptance Criteria

AC-001 能生成 Context Object

AC-002 能检索企业历史信息

AC-003 Evidence 包含来源

AC-004 Evidence 按相关度排序

AC-005 上下文变化时能够重新检索
