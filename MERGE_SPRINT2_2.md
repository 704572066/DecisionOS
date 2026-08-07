# 合并 Sprint 2-2

```bash
python3 scripts/apply_sprint2_2_patch.py
```

将 `.env.sprint2_2.example` 内容加入 `.env.prod`，并把
`docker-compose.prod.sprint2_2.patch.yml` 中 backend 环境变量合并进正式 Compose。

提交：

```bash
git add -A
git commit -m "feat: add Sprint 2-2 hybrid knowledge retriever"
git push
```

服务器：

```bash
git pull
docker compose --env-file .env.prod -f docker-compose.prod.yml build --no-cache backend
docker compose --env-file .env.prod -f docker-compose.prod.yml up -d
```

然后执行 pgvector SQL migration 和 embedding backfill。
