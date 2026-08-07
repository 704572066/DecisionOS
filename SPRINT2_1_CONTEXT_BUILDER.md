# Sprint 2-1 Context Builder

## 目标
把原 `analyze_meeting()` 中混合的文本分析拆成统一、可测试、可扩展的 Runtime Context 对象。当前不引入 Embedding、LLM 或 pgvector。

## 新接口
- `GET /api/meetings/{meetingId}/context`
- `POST /api/context/build`

## Context 字段
`contextId`、`projectId`、`meetingId`、`intent`、`currentObjective`、`transcriptWindow`、`topics`、`entities`、`keywords`、`facts`、`constraints`、`references`、`metadata`。

## 合并
```bash
python3 scripts/apply_sprint2_1_patch.py
```

## 构建
```bash
docker compose --env-file .env.prod -f docker-compose.prod.yml build --no-cache backend
docker compose --env-file .env.prod -f docker-compose.prod.yml up -d
```

## 验收
输入“客户A公司要求整体价格下降18%，付款周期延长到180天，并要求9月30日前完成交付”，应识别价格、付款、交付、客户，实体客户A公司，以及18%、180天、9月30日。
