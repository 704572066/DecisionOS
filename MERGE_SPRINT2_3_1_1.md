# 合并 Sprint 2-3.1.1

```bash
python3 scripts/apply_sprint2_3_1_1_patch.py
cat src/frontend/src/style.css.sprint2_3_1_1.append >> src/frontend/src/style.css
rm src/frontend/src/style.css.sprint2_3_1_1.append
```

`.env.prod`：

```env
REMINDER_ENABLE_THINKING=false
```

`docker-compose.prod.yml` backend：

```yaml
REMINDER_ENABLE_THINKING: ${REMINDER_ENABLE_THINKING:-false}
```

提交：

```bash
git add -A
git commit -m "perf: reduce AI reminder first-token latency"
git push
```
