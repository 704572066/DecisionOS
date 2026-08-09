# Sprint 3-2.3：Decision Surface

双栏：Transcript + Decision Board。

Reminder 改为 5 秒 Toast + Drawer；Evidence 进入独立 Drawer。
每次 `transcript.saved` 后 GET `/api/decision-board/{meetingId}`，只读取 Runtime State，不强制重新调用 LLM。

主 Board 只展示：目标、状态、决策成熟度、Top 2 风险、Top 2 行动、Top 3 待确认。

合并：

```bash
python scripts/apply_sprint3_2_3_patch.py
cat src/frontend/src/style.css.sprint3_2_3.append >> src/frontend/src/style.css
rm src/frontend/src/style.css.sprint3_2_3.append
cd src/frontend
npm run build
```
