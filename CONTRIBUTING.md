# Contributing to DecisionOS

## 基本原则

1. Git 仓库是项目文档与设计的唯一事实来源。
2. 重要产品或架构决策必须形成文档，不只保留在聊天或会议记录中。
3. 每次提交应聚焦一个明确目标，避免混合无关修改。
4. 未经评审的设想应标记为 Draft、Proposal 或 TBD。
5. 涉及产品边界的内容必须与 DOC-000 保持一致。

## 分支建议

当前早期阶段可直接使用 `master`。进入多人协作后建议采用：

- `master`：稳定、已评审内容
- `feature/<topic>`：新功能或新文档
- `docs/<topic>`：文档调整
- `fix/<topic>`：错误修复

## Commit 规范

```text
<type>: <summary>
```

常用类型：

- `docs`：文档内容
- `feat`：新增能力或代码
- `fix`：修复问题
- `refactor`：重构但不改变外部行为
- `chore`：仓库与工具维护
- `test`：测试与评测

示例：

```text
docs: initialize DecisionOS documentation structure
docs: define product boundaries in DOC-000
feat: add initial LLM gateway prototype
```

## 文档评审检查

- 是否说明目标读者与文档目的
- 是否使用统一术语
- 是否明确范围、非目标与假设
- 是否区分事实、决策、提案和待确认项
- 是否包含可验证的验收条件或后续行动
- 是否与上级文档存在冲突
