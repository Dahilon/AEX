"""
FastAPI middleware for automatic HTTP request metrics + run_id propagation.

Tracks latency, status codes, and error rates per endpoint.
Injects run_id into response headers for frontend correlation.
"""

import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from .metrics import emit_request_metrics
from .correlation import new_run_id, set_run_id

_SKIP_PATHS = ("/health", "/docs", "/openapi.json", "/favicon.ico")


class DatadogRequestMetrics(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        if request.url.path in _SKIP_PATHS:
            return await call_next(request)

        # Propagate or generate run_id
        rid = request.headers.get("x-run-id", "")
        if rid:
            set_run_id(rid)
        elif request.method == "POST":
            rid = new_run_id("req")

        start = time.time()
        response = await call_next(request)
        latency_ms = (time.time() - start) * 1000

        if rid:
            response.headers["x-run-id"] = rid

        path = self._normalize_path(request.url.path)
        emit_request_metrics(
            method=request.method,
            path=path,
            status_code=response.status_code,
            latency_ms=round(latency_ms, 1),
        )
        return response

    @staticmethod
    def _normalize_path(path: str) -> str:
        parts = path.strip("/").split("/")
        normalized = []
        for i, part in enumerate(parts):
            if i > 0 and parts[i - 1] == "agents" and part not in ("buy", "sell"):
                normalized.append("{agent_id}")
            else:
                normalized.append(part)
        return "/" + "/".join(normalized)
