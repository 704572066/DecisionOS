from __future__ import annotations

import html
import time
from datetime import datetime, timezone

from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from sqlalchemy import func, select, text

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.entities import (
    Decision,
    KnowledgeItem,
    Meeting,
    MeetingTranscriptSegment,
    Project,
    Task,
)
from app.observability.runtime_metrics import runtime_metrics

router = APIRouter()


def collect_health() -> tuple[dict, int]:
    started = time.perf_counter()
    database_status = "ok"
    database_error = None
    counts = {
        "projects": 0,
        "meetings": 0,
        "transcriptSegments": 0,
        "knowledgeItems": 0,
        "decisions": 0,
        "tasks": 0,
    }

    db = SessionLocal()
    try:
        db.execute(text("SELECT 1"))
        counts = {
            "projects": db.scalar(select(func.count()).select_from(Project)) or 0,
            "meetings": db.scalar(select(func.count()).select_from(Meeting)) or 0,
            "transcriptSegments": db.scalar(
                select(func.count()).select_from(MeetingTranscriptSegment)
            ) or 0,
            "knowledgeItems": db.scalar(
                select(func.count()).select_from(KnowledgeItem)
            ) or 0,
            "decisions": db.scalar(select(func.count()).select_from(Decision)) or 0,
            "tasks": db.scalar(select(func.count()).select_from(Task)) or 0,
        }
    except Exception as exc:
        database_status = "error"
        database_error = str(exc)
        runtime_metrics.record_error(
            category="health.database",
            message=database_error,
        )
    finally:
        db.close()

    metrics = runtime_metrics.snapshot()
    status = "ok" if database_status == "ok" else "degraded"
    payload = {
        "status": status,
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "version": "0.2.1",
        "environment": settings.app_environment,
        "asr": {
            "provider": settings.asr_provider,
            "language": settings.asr_language,
        },
        "database": {
            "status": database_status,
            "error": database_error,
            "checkDurationMs": round((time.perf_counter() - started) * 1000, 2),
        },
        "data": counts,
        "runtime": metrics,
    }
    return payload, 200 if status == "ok" else 503


@router.get("/health")
def health():
    payload, _ = collect_health()
    return payload


@router.get("/api/debug/status")
def debug_status_api():
    payload, _ = collect_health()
    return payload


@router.get("/debug/status", response_class=HTMLResponse)
def debug_status_page():
    # The page fetches live JSON every 5 seconds. No frontend rebuild is needed.
    title = html.escape(settings.app_name)
    return HTMLResponse(
        f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} 健康状态</title>
<style>
:root {{ font-family: Inter, "PingFang SC", "Microsoft YaHei", sans-serif; color:#172033; background:#f3f5f9; }}
body {{ margin:0; padding:24px; }}
main {{ max-width:1100px; margin:auto; }}
header {{ display:flex; justify-content:space-between; align-items:center; gap:16px; }}
h1 {{ margin:0 0 6px; }}
.badge {{ padding:7px 12px; border-radius:999px; font-weight:700; }}
.ok {{ background:#dcfae6; color:#067647; }}
.degraded {{ background:#fee4e2; color:#b42318; }}
.grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(210px,1fr)); gap:14px; margin:20px 0; }}
.card {{ background:white; border:1px solid #e3e7ef; border-radius:14px; padding:17px; box-shadow:0 4px 15px rgba(17,24,39,.05); }}
.card strong {{ display:block; color:#667085; font-size:13px; margin-bottom:7px; }}
.value {{ font-size:27px; font-weight:750; }}
table {{ width:100%; border-collapse:collapse; background:white; border-radius:14px; overflow:hidden; }}
th,td {{ padding:11px 13px; border-bottom:1px solid #e8ecf2; text-align:left; vertical-align:top; }}
th {{ background:#f8fafc; }}
pre {{ white-space:pre-wrap; word-break:break-word; margin:0; }}
footer {{ margin-top:18px; color:#667085; }}
</style>
</head>
<body>
<main>
<header>
<div><h1>{title} 健康检查</h1><div id="updated">正在加载……</div></div>
<div id="status" class="badge">检查中</div>
</header>
<div id="cards" class="grid"></div>
<section class="card">
<h2>最近异常</h2>
<table>
<thead><tr><th>时间</th><th>类别</th><th>Request ID</th><th>Meeting</th><th>信息</th></tr></thead>
<tbody id="errors"><tr><td colspan="5">暂无异常</td></tr></tbody>
</table>
</section>
<section class="card"><h2>完整状态</h2><pre id="raw"></pre></section>
<footer>页面每 5 秒自动刷新。接口：<code>/api/debug/status</code></footer>
</main>
<script>
function card(label, value) {{
  return `<div class="card"><strong>${{label}}</strong><div class="value">${{value}}</div></div>`;
}}
async function refresh() {{
  try {{
    const response = await fetch('/api/debug/status', {{cache:'no-store'}});
    const data = await response.json();
    const status = document.getElementById('status');
    status.textContent = data.status;
    status.className = 'badge ' + data.status;
    document.getElementById('updated').textContent = '更新时间：' + data.timestamp;
    const r = data.runtime;
    const d = data.data;
    document.getElementById('cards').innerHTML = [
      card('数据库', data.database.status),
      card('运行时长（秒）', r.uptimeSeconds),
      card('活跃 WebSocket', r.activeWebSocketCount),
      card('请求总数', r.requestsTotal),
      card('HTTP 错误', r.httpErrorsTotal),
      card('未处理异常', r.unhandledErrorsTotal),
      card('平均请求耗时（ms）', r.averageRequestDurationMs),
      card('最近提醒耗时（ms）', r.lastReminderDurationMs ?? '-'),
      card('项目', d.projects),
      card('会议', d.meetings),
      card('转写分段', d.transcriptSegments),
      card('知识条目', d.knowledgeItems)
    ].join('');
    const rows = r.recentErrors || [];
    document.getElementById('errors').innerHTML = rows.length
      ? rows.map(x => `<tr><td>${{x.timestamp}}</td><td>${{x.category}}</td><td>${{x.request_id || '-'}}</td><td>${{x.meeting_id || '-'}}</td><td>${{x.message}}</td></tr>`).join('')
      : '<tr><td colspan="5">暂无异常</td></tr>';
    document.getElementById('raw').textContent = JSON.stringify(data, null, 2);
  }} catch (error) {{
    const status = document.getElementById('status');
    status.textContent = 'offline';
    status.className = 'badge degraded';
    document.getElementById('updated').textContent = String(error);
  }}
}}
refresh();
setInterval(refresh, 5000);
</script>
</body>
</html>"""
    )
