
# 合并 Sprint 3-1.1

```bash
python3 scripts/apply_sprint3_1_1_patch.py

cat src/frontend/src/style.css.sprint3_1_1.append   >> src/frontend/src/style.css

rm src/frontend/src/style.css.sprint3_1_1.append

git add -A
git commit -m "fix: show decision modal and suppress duplicate reminders"
git push
```

服务器：

```bash
git pull

docker compose   --env-file .env.prod   -f docker-compose.prod.yml   build --no-cache backend frontend

docker compose   --env-file .env.prod   -f docker-compose.prod.yml   up -d
```
