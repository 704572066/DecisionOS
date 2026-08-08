# 合并 Sprint 2-3.1

```bash
python3 scripts/apply_sprint2_3_1_patch.py
cat src/frontend/src/style.css.sprint2_3_1.append >> src/frontend/src/style.css
rm src/frontend/src/style.css.sprint2_3_1.append

git add -A
git commit -m "feat: stream realtime AI reminders"
git push
```

服务器：

```bash
git pull
docker compose --env-file .env.prod -f docker-compose.prod.yml build --no-cache backend frontend
docker compose --env-file .env.prod -f docker-compose.prod.yml up -d
```
