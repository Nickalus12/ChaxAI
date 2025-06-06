"""Enhanced middleware for enterprise features."""

import time
import uuid
import logging
from typing import Dict, Optional
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from fastapi import status
import redis
from datetime import datetime, timedelta

from .config import (
    RATE_LIMIT_REQUESTS, RATE_LIMIT_WINDOW,
    ENABLE_MULTI_TENANT, DEFAULT_TENANT_ID
)

logger = logging.getLogger("chaxai.middleware")


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Attach unique request ID to each request."""
    
    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id
        
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = str(process_time)
        
        # Log request details
        logger.info(
            f"Request {request_id}: {request.method} {request.url.path} "
            f"- Status: {response.status_code} - Time: {process_time:.3f}s"
        )
        
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add comprehensive security headers."""
    
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        
        security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Content-Security-Policy": (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self' data:; "
                "connect-src 'self' https: wss:;"
            ),
            "Permissions-Policy": (
                "camera=(), microphone=(), geolocation=(), "
                "interest-cohort=()"
            ),
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        }
        
        for header, value in security_headers.items():
            response.headers[header] = value
        
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware using Redis."""
    
    def __init__(self, app):
        super().__init__(app)
        self.redis_client = None
        try:
            self.redis_client = redis.Redis(
                host='redis',
                port=6379,
                decode_responses=True
            )
            self.redis_client.ping()
        except Exception as e:
            logger.warning(f"Redis not available for rate limiting: {e}")
    
    async def dispatch(self, request: Request, call_next) -> Response:
        if not self.redis_client:
            return await call_next(request)
        
        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/", "/docs", "/openapi.json"]:
            return await call_next(request)
        
        # Get client identifier
        client_id = request.headers.get("X-API-Token", request.client.host)
        key = f"rate_limit:{client_id}"
        
        try:
            # Check rate limit
            current = self.redis_client.incr(key)
            if current == 1:
                self.redis_client.expire(key, RATE_LIMIT_WINDOW)
            
            if current > RATE_LIMIT_REQUESTS:
                logger.warning(f"Rate limit exceeded for {client_id}")
                return Response(
                    content="Rate limit exceeded",
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    headers={
                        "Retry-After": str(RATE_LIMIT_WINDOW),
                        "X-RateLimit-Limit": str(RATE_LIMIT_REQUESTS),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str(
                            int(time.time()) + RATE_LIMIT_WINDOW
                        ),
                    }
                )
            
            # Process request
            response = await call_next(request)
            
            # Add rate limit headers
            remaining = max(0, RATE_LIMIT_REQUESTS - current)
            response.headers["X-RateLimit-Limit"] = str(RATE_LIMIT_REQUESTS)
            response.headers["X-RateLimit-Remaining"] = str(remaining)
            response.headers["X-RateLimit-Reset"] = str(
                int(time.time()) + RATE_LIMIT_WINDOW
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Rate limiting error: {e}")
            return await call_next(request)


class TenantMiddleware(BaseHTTPMiddleware):
    """Multi-tenant isolation middleware."""
    
    async def dispatch(self, request: Request, call_next) -> Response:
        # Extract tenant ID from various sources
        tenant_id = None
        
        # 1. From header
        tenant_id = request.headers.get("X-Tenant-ID")
        
        # 2. From JWT token (if authenticated)
        if not tenant_id and hasattr(request.state, "user"):
            tenant_id = request.state.user.tenant_id
        
        # 3. From subdomain
        if not tenant_id:
            host = request.headers.get("host", "")
            if "." in host:
                subdomain = host.split(".")[0]
                if subdomain not in ["www", "api"]:
                    tenant_id = subdomain
        
        # 4. Default tenant
        if not tenant_id:
            tenant_id = DEFAULT_TENANT_ID
        
        # Store in request state
        request.state.tenant_id = tenant_id
        
        # Process request
        response = await call_next(request)
        
        # Add tenant header to response
        response.headers["X-Tenant-ID"] = tenant_id
        
        return response


class AuditMiddleware(BaseHTTPMiddleware):
    """Audit logging middleware for compliance."""
    
    async def dispatch(self, request: Request, call_next) -> Response:
        audit_logger = logging.getLogger("chaxai.audit")
        
        # Capture request details
        audit_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": getattr(request.state, "request_id", "unknown"),
            "method": request.method,
            "path": request.url.path,
            "client_host": request.client.host,
            "user_id": None,
            "tenant_id": getattr(request.state, "tenant_id", "unknown"),
        }
        
        # Add user info if authenticated
        if hasattr(request.state, "user"):
            audit_entry["user_id"] = request.state.user.user_id
            audit_entry["user_email"] = request.state.user.email
        
        # Process request
        start_time = time.time()
        response = await call_next(request)
        duration = time.time() - start_time
        
        # Complete audit entry
        audit_entry.update({
            "status_code": response.status_code,
            "duration_ms": int(duration * 1000),
            "success": 200 <= response.status_code < 400,
        })
        
        # Log audit entry
        audit_logger.info(json.dumps(audit_entry))
        
        return response