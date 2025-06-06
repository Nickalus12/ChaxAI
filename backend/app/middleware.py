from __future__ import annotations

import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

__all__ = ["RequestIDMiddleware"]


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Attach a unique request ID to each response."""

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = str(uuid.uuid4())
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
