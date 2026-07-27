# SPEC-001 ContextObject

Document ID: SPEC-001
Version: v0.1
Status: Draft
Owner: Architecture Team
Depends On:
- DOC-000
- DOC-001
- DOC-002
- DOC-003

---

# 1. Purpose

ContextObject 是 DecisionOS 的统一上下文对象。
所有 Context Engine、API、Prompt、数据库及前端模块均应使用本规范定义的数据结构。

---

# 2. Scope

适用于：

- Meeting Understanding
- Context Engine
- Decision Assistant
- Decision Memory
- API
- Data Model

---

# 3. Lifecycle

Raw Input
→ ContextObject
→ Context Retrieval
→ Evidence
→ Decision Memory

---

# 4. Object Definition

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| contextId | string | Yes | 上下文唯一标识 |
| meetingId | string | Yes | 当前会议ID |
| topic | string | Yes | 当前讨论主题 |
| participants | array | Yes | 参会人员 |
| customer | object | No | 客户信息 |
| project | object | No | 项目信息 |
| keywords | array | Yes | 当前关键词 |
| entities | array | Yes | 识别出的实体 |
| intent | string | Yes | 当前讨论意图 |
| riskLevel | enum | No | 风险等级 |
| timestamp | datetime | Yes | 更新时间 |

---

# 5. JSON Example

```json
{
  "contextId":"ctx-001",
  "meetingId":"meeting-001",
  "topic":"客户价格谈判",
  "participants":["CEO","Sales"],
  "keywords":["折扣","付款周期"],
  "entities":["客户A","合同203"],
  "intent":"NEGOTIATION",
  "riskLevel":"MEDIUM",
  "timestamp":"2026-07-26T15:00:00Z"
}
```

---

# 6. Validation Rules

- contextId MUST 唯一
- topic MUST 非空
- timestamp MUST 使用 ISO8601
- participants MUST 为数组
- keywords SHOULD 去重
- entities MAY 为空

---

# 7. Compatibility

新增字段不得影响旧版本解析。
字段删除需升级主版本号。

---

# 8. Acceptance Criteria

- 所有模块使用统一 ContextObject
- API 返回对象符合本规范
- 数据库存储字段与规范一致
- Prompt 输入对象与规范一致
