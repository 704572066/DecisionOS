# 合并 Sprint 2-1.3

```bash
python3 scripts/apply_sprint2_1_3_patch.py
git add -A
git commit -m "fix: canonicalize business context statements"
git push
```

服务器：

```bash
git pull
docker compose --env-file .env.prod -f docker-compose.prod.yml build --no-cache backend
docker compose --env-file .env.prod -f docker-compose.prod.yml up -d
```

不需要数据库迁移。
