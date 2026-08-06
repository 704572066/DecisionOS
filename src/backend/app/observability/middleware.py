from __future__ import annotations

import logging
import time
from uuid import uuid4

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.observability.runtime_metrics import runtime_metrics

logger = logging.getLogger("decisionos.http")


class RequestObservabilityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or uuid4().hex
        request.state.request_id = request_id
        started = time.perf_counter()
        runtime_metrics.request_started()

        try:
            response = await call_next(request)
        except Exception as exc:
            duration_ms = (time.perf_counter() - started) * 1000
            runtime_metrics.request_failed()
            runtime_metrics.record_error(
                category="http.unhandled",
                message=str(exc),
                request_id=request_id,
            )
            logger.exception(
                "Unhandled HTTP exception method=%s path=%s duration_ms=%.2f",
                request.method,
                request.url.path,
                duration_ms,
                extra={"request_id": request_id},
            )
            return JSONResponse(
                status_code=500,
                content={
                    "error": "internal_server_error",
                    "message": "服务器内部错误",
                    "requestId": request_id,
                },
                headers={"X-Request-ID": request_id},
            )

        duration_ms = (time.perf_counter() - started) * 1000
        runtime_metrics.request_finished(response.status_code, duration_ms)
        response.headers["X-Request-ID"] = request_id

        log_method = logger.warning if response.status_code >= 400 else logger.info
        log_method(
            "HTTP request method=%s path=%s status=%s duration_ms=%.2f",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
            extra={"request_id": request_id},
        )
        return response
