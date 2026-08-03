# 合并说明

将本压缩包内容复制到 DecisionOS 仓库根目录，允许覆盖同名文件。

重点新增：

```text
src/backend/app/asr/
src/backend/app/api/audio_ws.py
src/backend/app/services/transcript_service.py
src/backend/app/services/reminder_service.py
SPRINT1_REALTIME_VOICE.md
```

重点修改：

```text
src/backend/app/main.py
src/backend/app/models/entities.py
src/backend/app/api/routes.py
src/backend/app/core/config.py
src/backend/requirements.txt
src/frontend/src/main.tsx
src/frontend/src/style.css
src/frontend/src/vite-env.d.ts
src/frontend/Dockerfile.prod
deployment/nginx/decisionos.conf
docker-compose.prod.yml
.env.example
.env.prod.example
```

提交建议：

```bash
git add -A
git commit -m "feat: add Sprint 1 realtime voice meeting"
git push
```
