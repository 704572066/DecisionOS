# Sprint 3-1.1 JSX Hotfix

执行：

```bash
python3 scripts/apply_sprint3_1_1_jsx_hotfix.py
```

然后先验证前端：

```bash
cd src/frontend
npm run build
```

如果编译通过，再提交：

```bash
cd ../..
git add -A
git commit -m "fix: repair Sprint 3-1.1 decision modal JSX"
git push
```

服务器只需重建 frontend：

```bash
docker compose \
  --env-file .env.prod \
  -f docker-compose.prod.yml \
  build --no-cache frontend

docker compose \
  --env-file .env.prod \
  -f docker-compose.prod.yml \
  up -d frontend
```

本 Hotfix 不修改后端，也不需要数据库迁移。
