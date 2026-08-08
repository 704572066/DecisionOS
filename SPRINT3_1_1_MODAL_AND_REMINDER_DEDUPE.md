
# Sprint 3-1.1：Decision Modal + Reminder Semantic Dedupe

本版本只修两个 Demo 问题，不新增领域对象。

## Decision Candidate 弹窗

点击“生成决策”后，不再在页面底部展示 Decision Draft，而是打开 Modal。

支持：
- 点击遮罩关闭；
- 处理中禁止误关闭；
- 标题与 Decision Statement 编辑；
- 风险 / Evidence / Suggested Tasks 展示；
- 确认决策；
- 移动端适配。

## AI Reminder 去重

同一 meeting 下使用：

```text
cleanTranscriptWindow
+
normalized facts
```

构造语义指纹。

如果用户重复说：

```text
客户要求整体价格下降18%，并希望付款周期延长到180天。
```

而 Cleaner 最终仍得到同一 Canonical Context，则：

```text
直接跳过 Retriever / Reranker / LLM
```

不会再次生成 Reminder，也不会重复消耗模型 token。

当业务事实变化，例如：

```text
180天 → 120天
18% → 12%
新增交付时间
```

会形成新的指纹，允许生成新 Reminder。

## 合并

```bash
python3 scripts/apply_sprint3_1_1_patch.py

cat src/frontend/src/style.css.sprint3_1_1.append   >> src/frontend/src/style.css

rm src/frontend/src/style.css.sprint3_1_1.append
```

重新构建 backend + frontend 即可，无需数据库迁移。
