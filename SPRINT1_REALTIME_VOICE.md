# Sprint 1：实时语音会议

## 已实现

- 浏览器麦克风实时输入。
- Browser Web Speech API 模式，无需 ASR 密钥。
- Deepgram 流式 ASR 模式，浏览器通过 MediaRecorder 每 300ms 发送音频分片。
- FastAPI WebSocket：`/api/meetings/{meetingId}/audio-stream`。
- partial/final 转写事件。
- final 转写持久化为 `meeting_transcript_segments`。
- final 转写自动追加到 Meeting transcript。
- 按新增文本长度与冷却时间触发历史提醒。
- 相同来源提醒会话内去重。
- Nginx WebSocket 反向代理。
- 手工文本调试入口保留。

## 运行模式

### Browser 模式

适合最快验证：

```env
ASR_PROVIDER=browser
```

前端使用 Chrome/Edge 的 Web Speech API。服务端接收最终文本并触发提醒。

### Deepgram 模式

```env
ASR_PROVIDER=deepgram
DEEPGRAM_API_KEY=你的密钥
```

前端选择“Deepgram 流式音频”，浏览器音频分片经 DecisionOS 后端转发给 Deepgram。

## HTTPS

公网麦克风必须通过 HTTPS 页面访问。HTTP 公网 IP 通常无法调用 `getUserMedia()`。

## 部署

```bash
docker compose --env-file .env.prod -f docker-compose.prod.yml up -d --build
```

只重建前后端：

```bash
docker compose --env-file .env.prod -f docker-compose.prod.yml build --no-cache backend frontend
docker compose --env-file .env.prod -f docker-compose.prod.yml up -d
```

## 数据库

应用启动时 SQLAlchemy 会自动创建新表：

```text
meeting_transcript_segments
```

当前 Demo 不使用迁移工具；后续进入正式开发时应接入 Alembic。
