# 合并 Sprint 2-3

复制压缩包到 DecisionOS 根目录后：

```bash
python3 scripts/apply_sprint2_3_patch.py
python3 scripts/apply_frontend_sprint2_3_patch.py
cat src/frontend/src/style.css.sprint2_3.append >> src/frontend/src/style.css
rm src/frontend/src/style.css.sprint2_3.append
```

将 `.env.sprint2_3.example` 中配置加入 `.env.prod`，
把 `docker-compose.prod.sprint2_3.patch.yml` 中 backend 环境变量合并进正式 Compose。

提交：

```bash
git add -A
git commit -m "feat: add Sprint 2-3 AI reminder engine"
git push
```

服务器：

```bash
git pull

docker compose   --env-file .env.prod   -f docker-compose.prod.yml   build --no-cache backend frontend

docker compose   --env-file .env.prod   -f docker-compose.prod.yml   up -d
```

验证：

```bash
curl -X POST   http://127.0.0.1/api/reminders/meetings/meeting-83e6181f64c7/generate
```
