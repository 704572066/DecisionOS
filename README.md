# DecisionOS

> Enterprise Context Intelligence Platform · 企业上下文智能平台

DecisionOS 面向企业经营者、创业者与管理团队，通过统一企业上下文、长期知识记忆和可追溯证据，为组织提供可解释、可执行、可复盘的决策支持。

## 当前阶段

项目处于 **Repository v1.0 / Architecture Baseline** 阶段。产品边界、Context Engine、ContextObject 与 Knowledge Object Model 已形成初始基线，下一阶段进入 System Context 与 System Architecture。

## 文档入口

- [文档中心](docs/README.md)
- [路线图](ROADMAP.md)
- [贡献指南](CONTRIBUTING.md)
- [变更记录](CHANGELOG.md)

## 仓库结构

```text
DecisionOS/
├── docs/          # 产品、架构、规范、ADR 与图表
├── schemas/       # JSON Schema 等机器可读契约
├── examples/      # 可复用示例数据
├── src/           # 后端、前端与 AI 服务实现
├── api/           # 保留现有 API 设计资产
├── database/      # 保留现有数据库设计资产
├── deployment/    # 保留现有部署资产
├── prompts/       # 保留现有 Prompt 与 Agent 资产
├── hardware/      # 可选硬件设计
└── prototype/     # 原型与验证代码
```

## 核心原则

- AI 提供 Evidence 与 Context，管理者负责最终决策。
- ContextObject 是运行时上下文快照，不是业务实体。
- Knowledge Object 是可引用、可追溯、可关联的长期业务对象。
- 正式设计遵循 `Draft → Review → Approved → Deprecated` 生命周期。

## 状态声明

项目仍处于早期设计阶段。未标记为 `Approved` 的内容可能随评审和原型验证调整。
