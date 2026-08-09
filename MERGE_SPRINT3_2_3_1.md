# 合并 Sprint 3-2.3.1

```bash
python scripts/apply_sprint3_2_3_1_patch.py

cd src/frontend
npm run build
```

编译通过：

```bash
cd ../..
git add -A
git commit -m "fix: let decision board sections size to content"
git push
```

服务器只需重建 frontend。
