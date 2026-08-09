# 合并 Sprint 3-2.1
```bash
python3 scripts/apply_sprint3_2_1_patch.py
git add -A
git commit -m "feat: add runtime state and decision board engine"
git push
```
服务器：
```bash
git pull
docker compose --env-file .env.prod -f docker-compose.prod.yml build --no-cache backend
docker compose --env-file .env.prod -f docker-compose.prod.yml up -d backend
```
无需数据库迁移。
