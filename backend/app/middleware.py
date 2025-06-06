from __future__ import annotations

import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

__all__ = ["RequestIDMiddleware", "SecurityHeadersMiddleware"]


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Attach a unique request ID to each response."""

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = str(uuid.uuid4())
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add basic security headers to each response."""

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "Referrer-Policy": "same-origin",
            "Content-Security-Policy": "default-src 'self'",
        }
        for name, value in headers.items():
            response.headers.setdefault(name, value)
        return response
