# 合并 Sprint 3-1
```bash
python3 scripts/apply_sprint3_1_patch.py
cat src/frontend/src/style.css.sprint3_1.append >> src/frontend/src/style.css
rm src/frontend/src/style.css.sprint3_1.append
git add -A
git commit -m "feat: add Sprint 3-1 decision candidate loop"
git push
```
服务器重建 backend/frontend 即可；不需要数据库迁移。
