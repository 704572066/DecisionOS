# 合并 Sprint 3-2.2

```bash
python3 scripts/apply_sprint3_2_2_patch.py

git add -A
git commit -m "feat: add runtime decision event updates"
git push
```

服务器：

```bash
git pull

docker compose \
  --env-file .env.prod \
  -f docker-compose.prod.yml \
  build --no-cache backend

docker compose \
  --env-file .env.prod \
  -f docker-compose.prod.yml \
  up -d backend
```

无需数据库迁移。
