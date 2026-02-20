"""
FastAPI middleware for automatic HTTP request metrics.

Tracks latency, status codes, and error rates per endpoint —
equivalent to APM service metrics without needing ddtrace instrumentation.
"""

import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from .metrics import emit_request_metrics


class DatadogRequestMetrics(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        if request.url.path in ("/health", "/docs", "/openapi.json"):
            return await call_next(request)

        start = time.time()
        response = await call_next(request)
        latency_ms = (time.time() - start) * 1000

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
        """Collapse dynamic path segments to reduce cardinality."""
        parts = path.strip("/").split("/")
        normalized = []
        for i, part in enumerate(parts):
            if i > 0 and parts[i - 1] == "agents" and part not in ("buy", "sell"):
                normalized.append("{agent_id}")
            else:
                normalized.append(part)
        return "/" + "/".join(normalized)
