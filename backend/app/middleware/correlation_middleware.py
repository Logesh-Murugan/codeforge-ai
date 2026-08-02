"""
CorrelationMiddleware — Phase 5.11

Propagates X-Correlation-ID HTTP header and tracks request execution duration.
"""
from __future__ import annotations

import time
import uuid
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.core.observability import observability


class CorrelationMiddleware(BaseHTTPMiddleware):
    """
    HTTP Request Correlation ID & Response Timing Middleware.
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        correlation_id = request.headers.get("X-Correlation-ID", f"CORR-{uuid.uuid4().hex[:8]}")
        t0 = time.perf_counter()

        response: Response = await call_next(request)

        duration_ms = (time.perf_counter() - t0) * 1000.0
        response.headers["X-Correlation-ID"] = correlation_id
        response.headers["X-Response-Time-Ms"] = f"{duration_ms:.2f}"

        observability.log_event(
            "http_request_completed",
            correlation_id=correlation_id,
            path=request.url.path,
            method=request.method,
            status_code=response.status_code,
            duration_ms=round(duration_ms, 2),
        )

        return response
