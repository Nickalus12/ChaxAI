"""Simple API token security utilities."""

from fastapi import Depends, HTTPException
from fastapi.security import APIKeyHeader
from starlette.status import HTTP_403_FORBIDDEN

from .config import API_TOKENS
import hmac

api_key_header = APIKeyHeader(name="X-API-Token", auto_error=False)


def verify_token(token: str | None = Depends(api_key_header)) -> None:
    """Raise HTTP 403 if the supplied token is invalid."""
    if not API_TOKENS:
        return
    if token is None:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail="Invalid or missing API token",
        )
    for valid in API_TOKENS:
        if hmac.compare_digest(valid, token):
            return
    raise HTTPException(
        status_code=HTTP_403_FORBIDDEN,
        detail="Invalid or missing API token",
    )
