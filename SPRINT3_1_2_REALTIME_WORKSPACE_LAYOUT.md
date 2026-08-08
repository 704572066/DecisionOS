# Sprint 3-1.2：Realtime Workspace Layout

目标：让 Transcript 与 AI Reminder 保持等高，并分别内部滚动。

## 改动

- Transcript 固定高度、内部滚动、自动滚到底部；
- AI Reminder 与 Transcript 同高；
- Streaming Reminder 固定在 Reminder 顶部；
- 已完成 Reminder 最多保留最近 5 条；
- 不修改后端；
- 不修改 Decision Candidate Modal；
- 不需要数据库迁移。

## 合并

```bash
python3 scripts/apply_sprint3_1_2_patch.py

cat src/frontend/src/style.css.sprint3_1_2.append \
  >> src/frontend/src/style.css

rm src/frontend/src/style.css.sprint3_1_2.append
```

先验证：

```bash
cd src/frontend
npm run build
```

验收重点：
1. Transcript / Reminder 两列等高；
2. Transcript 只在自身区域滚动；
3. Reminder 不再撑高页面；
4. Streaming Reminder 在顶部；
5. 最多显示最近 5 条正式提醒。
