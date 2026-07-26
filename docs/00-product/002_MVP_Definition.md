# MVP Definition

Title: MVP Definition
Document ID: DOC-002
Version: v0.1
Status: Draft
Owner: Product Team
Dependencies:
- DOC-000 Product Constitution
- DOC-001 Product Vision
Last Updated: 2026-07-26

---

# 1. Document Purpose

本文档定义 DecisionOS V0.1 的最小可行产品（MVP）范围，并作为产品、研发、测试共同遵循的开发基线。

# 2. MVP Goal

验证 DecisionOS 的核心价值：

在真实会议过程中，系统能够主动提供与当前议题相关的企业上下文，并帮助管理者完成决策。

# 3. Core Workflow

会议开始
→ 获取实时文本（ASR）
→ 理解当前讨论主题
→ 检索企业上下文
→ 主动推送相关证据
→ 会议结束
→ 生成决策记录

# 4. Functional Modules

## M1 Meeting Understanding
目标：识别会议主题、关键词、人物、客户、项目。

输入：
- 实时文本流

输出：
- Context Object

验收：
- 能持续接收文本
- 能输出结构化上下文

## M2 Context Retrieval

目标：
根据 Context Object 检索企业历史信息。

输出包括：
- 历史会议
- 合同
- 项目
- 客户
- 决策记录

所有结果必须包含来源。

## M3 Decision Assistant

主动展示与当前议题相关的企业证据。

要求：
- 非聊天模式
- 可追溯
- 支持引用来源

## M4 Decision Memory

会议结束后自动生成：

- 决策事项
- 决策依据
- Owner
- 待办事项

## M5 Management Console

提供基础 Web 管理界面：

- 企业知识管理
- 决策记录查询
- Context 浏览

# 5. Non-Functional Requirements

- 响应时间：上下文检索≤3秒
- 所有 AI 输出必须包含来源
- 支持持续扩展企业知识

# 6. Out Of Scope

V0.1 不包含：

- 自动决策
- 自动执行
- 企业 IM
- OA/ERP/CRM
- 硬件终端
- 多 Agent 协同

# 7. Acceptance Criteria

AC-001 实时接收会议文本

AC-002 输出结构化 Context

AC-003 检索相关企业上下文

AC-004 AI 输出包含引用来源

AC-005 自动生成决策记录

# 8. Release Criteria

满足全部 Acceptance Criteria 后，可发布 DecisionOS V0.1。
