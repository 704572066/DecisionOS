# 全局异常日志与健康检查页面

## 合并

1. 将本包复制到 DecisionOS 根目录，覆盖同名文件。
2. 执行补丁脚本：

```bash
python3 scripts/apply_observability_patch.py
```

3. 将 `.env.observability.example` 中三项合并到 `.env.prod`：

```env
APP_NAME=DecisionOS Demo API
APP_ENVIRONMENT=production
LOG_LEVEL=INFO
```

4. 可选择将 `docker-compose.prod.observability.patch.yml` 的环境变量合并到现有
   `docker-compose.prod.yml`；即使不合并，代码也有默认值。

## 新增地址

- 基础健康接口：`/health`
- JSON 调试状态：`/api/debug/status`
- 健康检查页面：`/debug/status`

## 日志内容

HTTP 请求统一记录：

- Request ID
- 方法和路径
- HTTP 状态码
- 请求耗时
- 未处理异常堆栈

WebSocket/ASR 异常记录：

- Meeting ID
- 异常类别
- 异常信息

响应头会返回：

```text
X-Request-ID
```

前端或调用方报告异常时，应同时提供该 Request ID。

## 健康页指标

- 数据库状态和检测耗时
- 进程运行时间
- 请求总量、正在处理数量、错误数量
- 平均请求耗时
- 活跃 WebSocket 数量及 Meeting ID
- 最近一次 Reminder 耗时
- Project / Meeting / Transcript / Knowledge / Decision / Task 数量
- 最近 20 条运行时异常

## 部署

```bash
docker compose \
  --env-file .env.prod \
  -f docker-compose.prod.yml \
  build --no-cache backend

docker compose \
  --env-file .env.prod \
  -f docker-compose.prod.yml \
  up -d

docker compose \
  --env-file .env.prod \
  -f docker-compose.prod.yml \
  restart gateway
```

检查：

```bash
curl http://127.0.0.1/health
curl http://127.0.0.1/api/debug/status
```

浏览器：

```text
http://服务器IP/debug/status
```

## 当前边界

运行指标和最近异常保存在单个后端进程内存中，容器重启后清空。
这适合当前单实例 Demo。未来扩展多实例时，应接入 Prometheus、OpenTelemetry
或集中日志平台。
