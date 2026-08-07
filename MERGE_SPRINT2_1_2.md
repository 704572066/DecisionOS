# 合并 Sprint 2-1.2

将压缩包内容复制到 DecisionOS 根目录并覆盖同名文件。

```bash
git add -A
git commit -m "fix: consolidate business transcript sentences"
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
  up -d
```

本次不修改数据库，不需要迁移或删除数据卷。
