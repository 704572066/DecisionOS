# Sprint 2-2：Hybrid Knowledge Retriever

## 目标

将 Context Builder 输出升级为真正的企业记忆检索：

```text
BusinessContext
      ↓
Retrieval Query Builder
      ↓
Keyword Search ─┐
                 ├── Hybrid Fusion → Top-K Knowledge
Vector Search ──┘
```

## 技术

- PostgreSQL 16
- pgvector cosine similarity
- Keyword weighted retrieval
- Hybrid rank fusion
- Project Boundary 强制过滤
- OpenAI-compatible Embeddings

当前生产 Compose 已使用 `pgvector/pgvector:pg16`，无需新增数据库容器。

## 新 API

- `POST /api/retrieval/search`
- `GET /api/retrieval/meetings/{meetingId}?topK=8`
- `GET /api/retrieval/coverage`
- `POST /api/retrieval/admin/backfill`

未配置 Embedding 时自动返回 `mode=keyword`；配置并完成 backfill 后返回 `mode=hybrid`。

## 数据库

默认向量维度为 1536。首次部署执行：

```bash
cat scripts/sprint2_2_pgvector_1536.sql | \
docker compose --env-file .env.prod -f docker-compose.prod.yml exec -T db \
sh -lc 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"' 
```

如果使用其他维度的 Embedding 模型，应在创建向量列之前修改 SQL 和 `EMBEDDING_DIMENSIONS`。

## Embedding 配置

```env
EMBEDDING_BASE_URL=https://api.openai.com/v1
EMBEDDING_API_KEY=...
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIMENSIONS=1536
```

也可使用兼容 `/embeddings` API 的其他服务。

## Backfill

```bash
curl -X POST http://127.0.0.1/api/retrieval/admin/backfill \
  -H 'Content-Type: application/json' \
  -d '{"batchSize":16,"force":false}'
```

## 验证

```bash
curl http://127.0.0.1/api/retrieval/coverage

curl \
  'http://127.0.0.1/api/retrieval/meetings/meeting-83e6181f64c7?topK=8'
```

Sprint 2-2 先独立验证 Retriever，不立即替换实时 Reminder。下一阶段再把 Hybrid Retriever 正式接入 Prompt/Reminder。
