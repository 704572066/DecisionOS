# DecisionOS 文档中心

## 文档体系

| 目录 | 内容 | 当前状态 |
|---|---|---|
| `00-product` | 产品定义、愿景、原则、术语 | 进行中 |
| `01-requirements` | PRD、用户角色、场景、MVP | 待开始 |
| `02-architecture` | 总体架构、领域模型、集成架构 | 待开始 |
| `03-ai` | Decision Brain、Agent、知识与记忆 | 待开始 |
| `04-data` | 数据模型、事件模型、数据治理 | 待开始 |
| `05-api` | API 规范、接口定义、集成协议 | 待开始 |
| `06-security` | 权限、审计、隐私、AI 安全 | 待开始 |
| `07-deployment` | 部署、运维、可观测性与容灾 | 待开始 |
| `templates` | 文档模板与写作规范 | 已建立 |

## 文档编号

文档文件名采用：

```text
<类型>-<三位编号>_<英文标题>.md
```

示例：

```text
DOC-000_Product_Definition.md
PRD-001_Product_Requirements.md
ARC-001_System_Architecture.md
AI-001_Decision_Brain.md
SEC-001_Security_Architecture.md
```

推荐类型：

| 类型 | 用途 |
|---|---|
| `DOC` | 产品级基础定义与通用规范 |
| `PRD` | 产品需求文档 |
| `ARC` | 系统与软件架构 |
| `AI` | AI、Agent、知识、记忆和评测 |
| `DATA` | 数据架构与数据模型 |
| `API` | API 与集成协议 |
| `SEC` | 安全、隐私、合规与审计 |
| `OPS` | 部署、运维和可观测性 |
| `ADR` | 架构决策记录 |

## 文档状态

- `Draft`：草稿，尚未完成评审
- `Review`：正在评审
- `Approved`：已批准，作为后续设计依据
- `Deprecated`：已废弃，应指向替代文档

## 当前阅读顺序

1. [DOC-000 产品定义说明书](00-product/DOC-000_Product_Definition.md)
2. 后续：PRD-001 产品需求说明书
3. 后续：能力模型与 MVP 定义
4. 后续：总体架构说明书
