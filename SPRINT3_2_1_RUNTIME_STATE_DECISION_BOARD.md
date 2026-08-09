# Sprint 3-2.1：Runtime State + Decision Board Backend

目标：不增加数据库表，引入进程内 Runtime State，并基于现有 AI Reminder 一次运行结果构建有界 Decision Board。

新增 API：
- `GET /api/decision-board/{meetingId}`：优先读缓存，无缓存自动构建。
- `POST /api/decision-board/{meetingId}/refresh`：强制刷新 Context / Retrieval / Reminder / Runtime State / Board。

Decision Board：Risks<=3、Evidence<=5、Actions<=3、Todos<=5；第一版不额外调用 LLM。

合并：
```bash
python3 scripts/apply_sprint3_2_1_patch.py
```
无需数据库迁移。验证：
```bash
curl http://127.0.0.1/api/decision-board/meeting-83e6181f64c7
curl -X POST http://127.0.0.1/api/decision-board/meeting-83e6181f64c7/refresh
```
