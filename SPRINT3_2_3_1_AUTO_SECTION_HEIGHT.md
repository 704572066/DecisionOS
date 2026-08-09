# Sprint 3-2.3.1：Decision Board Auto Section Height

## 目标

Decision Board 整体仍保持固定高度和内部滚动，但：

- Top Risks
- Actions
- Todos

三个 section 不再分配固定高度或平均高度，而是根据内容自然撑开。

## 布局原则

```text
Decision Board（固定总高度）
└─ decision-board-scroll（统一滚动）
   ├─ Overview      auto
   ├─ Top Risks     auto
   ├─ Actions       auto
   ├─ Todos         auto
   └─ Links         auto
```

因此：

- 只有 1 条 Risk 时只占 1 条所需高度；
- 有 2 条 Risk 时自然增加；
- Actions/Todos 同理；
- 整体超出右侧面板高度时，由 Decision Board 统一滚动；
- section 自身不再产生第二层滚动条。

## 合并

```bash
python scripts/apply_sprint3_2_3_1_patch.py

cd src/frontend
npm run build
```

无需数据库迁移，也无需修改 backend。
