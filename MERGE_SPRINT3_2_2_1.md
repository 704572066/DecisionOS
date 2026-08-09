# 合并 Sprint 3-2.2.1

```bash
python scripts/apply_sprint3_2_2_1_patch.py
git diff src/backend/app/runtime/service.py
git add -A
git commit -m "fix: bootstrap runtime decision facts from context"
git push
```

服务器重新构建 backend 即可，无需数据库迁移。
