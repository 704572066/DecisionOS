# Bug Fix Sprint 1.1

## 本次目标

- 页面刷新后恢复当前 Meeting 和历史 transcript。
- WebSocket 断开后明确提示，并允许用户手动重新连接。
- Browser SpeechRecognition 自动结束后延迟重启，避免重复 start 异常。
- 对麦克风拒绝、麦克风缺失、设备占用等情况显示明确提示。
- final transcript 精确去重。
- 处理浏览器偶发的 `A`、`A+B` 连续 final：用较完整文本替换上一段。
- Reminder 在前后端均进行会话级去重。
- 后端 WebSocket 在断开或异常后可靠取消任务、关闭 ASR Provider。
- 增加 Meeting session localStorage 恢复。
- 增加 20 秒 WebSocket 心跳。

## 合并方式

将压缩包复制到仓库根目录并覆盖同名文件。

`src/frontend/src/style.css.append` 的内容需要追加到现有：

```text
src/frontend/src/style.css
```

然后删除 `.append` 文件。

## 构建

```bash
docker compose \
  --env-file .env.prod \
  -f docker-compose.prod.yml \
  build --no-cache backend frontend

docker compose \
  --env-file .env.prod \
  -f docker-compose.prod.yml \
  up -d
```

## 手工验收

1. 导入示例知识并创建会议。
2. 开始录音，连续讲话至少 5 分钟。
3. 等待 Chrome 自动结束一次 SpeechRecognition，确认系统会自动恢复。
4. 停止录音并刷新页面，确认 Meeting 与 transcript 恢复。
5. 重新开始录音。
6. 在录音中重启 gateway，确认页面提示连接断开并显示“重新连接”。
7. 连续说相似句子，确认 transcript 不重复。
8. 说“付款周期延长到180天”，确认提醒不会重复刷屏。

## 当前边界

- Reminder 去重仍是进程内状态，后端重启后会清空。
- 自动 WebSocket 重连没有默认开启，避免浏览器在未知状态下自动重新启动麦克风；用户通过按钮明确恢复。
- 数据库仍由 SQLAlchemy `create_all` 管理，正式版本应接入 Alembic。
