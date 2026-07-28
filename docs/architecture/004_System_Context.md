# 004 系统上下文（System Context）

> **文档编号：** 004\
> **架构视图：** C4 Model - Level 1（System Context）\
> **状态：** Draft\
> **版本：** v0.1.0\
> **最后更新：** 2026-07-28

------------------------------------------------------------------------

## 1. 文档目的

本文档定义 DecisionOS 的系统边界（System
Boundary），描述系统与用户及外部系统之间的关系。

本文档回答一个核心问题：

> **DecisionOS 负责什么？哪些能力属于 DecisionOS？哪些属于外部系统？**

## 2. 文档范围

### 包含

-   系统边界
-   外部参与者
-   外部系统
-   核心职责
-   系统上下文图
-   架构原则

### 不包含

-   服务拆分
-   数据库设计
-   API 设计
-   部署架构
-   领域模型
-   代码实现

## 3. 系统使命

DecisionOS 是企业上下文智能平台（Enterprise Context Intelligence
Platform），持续采集、组织、关联和分析企业知识，为管理者提供可信、可追溯的决策上下文。

平台辅助决策，而不是替代决策。

## 4. 外部参与者

### 决策者

-   查看上下文
-   查看 AI 建议
-   查看证据
-   做出最终决策

### 员工

-   上传文档
-   更新任务
-   参与会议
-   提供业务信息

### 系统管理员

-   用户管理
-   权限管理
-   AI 模型配置
-   系统运维

## 5. 外部系统

-   大语言模型（OpenAI、DeepSeek、Qwen、本地模型等）
-   企业业务系统（ERP、CRM、OA、HR、Wiki、Git 等）
-   身份认证系统（OAuth2 / OIDC / 企业 SSO）
-   对象存储（MinIO、S3 等）

## 6. 系统边界

DecisionOS 包含以下核心能力：

-   Web / Desktop Client
-   Context Engine
-   Knowledge Service
-   AI Service
-   Search Service
-   Workflow Service
-   API Gateway
-   Event Bus
-   Storage

## 7. 系统上下文图

``` mermaid
flowchart LR
DecisionMaker["决策者"]
Employee["员工"]
Administrator["管理员"]
subgraph DecisionOS
Client["Web/Desktop"]
Context["Context Engine"]
Knowledge["Knowledge Service"]
AI["AI Service"]
Search["Search Service"]
Workflow["Workflow Service"]
end
LLM["LLM"]
Storage["Object Storage"]
Enterprise["Enterprise Systems"]
Identity["Identity Provider"]
DecisionMaker-->Client
Employee-->Client
Administrator-->Client
Client-->Context
Client-->Knowledge
Client-->AI
Client-->Search
Client-->Workflow
Context-->Enterprise
Knowledge-->Storage
AI-->LLM
Client-->Identity
```

## 8. 系统职责

### DecisionOS 负责

-   构建企业上下文
-   管理企业知识
-   AI 推理
-   证据管理
-   语义检索
-   决策支持

### DecisionOS 不负责

-   ERP
-   CRM
-   财务系统
-   邮件系统
-   即时通讯

## 9. 架构原则

-   Context First
-   Evidence Driven
-   Human in Control
-   AI Native
-   Vendor Neutral
-   Pluggable Architecture

## 10. 关联文档

-   Product Vision
-   003_Context_Engine.md
-   005_System_Architecture.md
-   006_Deployment_Architecture.md
-   Knowledge Object Model
