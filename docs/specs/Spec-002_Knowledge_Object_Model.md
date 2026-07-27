SPEC-002 Knowledge Object Model

Purpose: 定义统一知识对象模型。

Core Objects:
Organization
Person
Meeting
Customer
Project
Contract
Decision
Task
Document
Risk

Base Object:
id
createdAt
updatedAt
createdBy
version

Boundary:
ContextObject不是Knowledge Object。
Evidence引用Knowledge Object。
