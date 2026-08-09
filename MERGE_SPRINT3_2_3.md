# 合并 Sprint 3-2.3

```bash
python scripts/apply_sprint3_2_3_patch.py
cat src/frontend/src/style.css.sprint3_2_3.append >> src/frontend/src/style.css
rm src/frontend/src/style.css.sprint3_2_3.append

cd src/frontend
npm run build
```

通过后提交并只重建 frontend。无需数据库迁移。
