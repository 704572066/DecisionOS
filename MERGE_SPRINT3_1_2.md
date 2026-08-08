# 合并 Sprint 3-1.2

```bash
python3 scripts/apply_sprint3_1_2_patch.py

cat src/frontend/src/style.css.sprint3_1_2.append \
  >> src/frontend/src/style.css

rm src/frontend/src/style.css.sprint3_1_2.append

cd src/frontend
npm run build
```

通过后：

```bash
cd ../..
git add -A
git commit -m "feat: balance realtime transcript and reminder workspace"
git push
```

服务器：

```bash
git pull

docker compose \
  --env-file .env.prod \
  -f docker-compose.prod.yml \
  build --no-cache frontend

docker compose \
  --env-file .env.prod \
  -f docker-compose.prod.yml \
  up -d frontend
```
