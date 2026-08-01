# DecisionOS Specification Index

## Introduction

DecisionOS Specification 是 DecisionOS 的官方设计规范。

本文档用于说明：

- 文档组织方式
- 阅读顺序
- 文档依赖关系
- 当前版本状态

---

# Reading Order

## Foundation

000 Design Principles

整个系统的设计原则。

---

## Product

001 Product Constitution

定义产品定位。

001 Product Vision

定义产品愿景。

002 MVP Definition

定义 MVP 范围。

---

## Architecture

003 Context Engine

Context Engine 总体架构。

004 System Context

系统边界。

005 System Architecture

系统总体架构。

006 Runtime Architecture

运行时架构。

007 Data Architecture

数据架构。

---

## Meta Model

001 Domain Overview

定义领域模型。

002 Domain Object Model

定义对象模型。

003 Common Object Specification

定义对象公共规范。

004 Relationship Model

定义对象关系。

005 Knowledge Object Model

定义知识对象。

---

## Runtime Model

006 Context Session Specification

定义一次运行时会话。

007 Context Specification

定义运行时上下文。

---

## Domain Model

008 Meeting Specification

协作事件。

009 Decision Specification

企业正式决策。

010 Evidence Specification

业务事实。

011 Task Specification

业务执行。

012 Project Specification

业务边界。

013 Document Specification

知识载体。

---

## Capability Foundation

014 Enterprise Knowledge Model

企业知识组织模型。

---

# Dependency

Design Principles

↓

Architecture

↓

Meta Model

↓

Runtime

↓

Domain

↓

Capability

---

# Status

| Category | Status |
|----------|--------|
| Foundation | ✅ |
| Product | ✅ |
| Architecture | ✅ |
| Meta Model | ✅ |
| Runtime | ✅ |
| Domain | ✅ |
| Capability Foundation | ✅ |

---

# Next Phase

- Knowledge Network
- Knowledge Engine
- Context Builder
- Retrieval
- Governance
- Schema
- API