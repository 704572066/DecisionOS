# DecisionOS Dialogue Foundation v1

Based on uploaded `src(5).zip`.

## New modules

- `backend/app/dialogue/models.py`
- `backend/app/dialogue/store.py`
- `backend/app/dialogue/agent.py`
- `backend/app/dialogue/service.py`
- `backend/app/dialogue/__init__.py`
- `backend/app/api/dialogue.py`

`backend/app/main.py` registers the new router.

## Architecture

`DialogueService` reads the same `RuntimeState` and `ReasoningResult`
as DecisionBoard, but it does **not** depend on DecisionBoard.

## API

Ask:

```bash
curl -X POST http://127.0.0.1/api/dialogue/<meeting-id> \
  -H 'Content-Type: application/json' \
  -d '{"text":"刚才客户最终接受多少折扣？"}'
```

Reset conversation history:

```bash
curl -X DELETE http://127.0.0.1/api/dialogue/<meeting-id>
```

## First validation questions

For `meeting-865a2b75abe4`:

1. `刚才客户最终接受多少折扣？`
2. `15%的方案现在是什么状态？`
3. `为什么现在没有风险提醒？`
4. `你怎么看现在这个方案？`

The current state should allow the agent to distinguish:
- 15% = our rejected commitment
- 10% = customer's confirmed requirement
- no current Finding for `discountPercent > 10`
