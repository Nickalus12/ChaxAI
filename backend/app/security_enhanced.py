"""Enhanced security module with JWT and multi-tenant support."""

import jwt
import bcrypt
from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import logging

from .config import (
    JWT_SECRET_KEY, JWT_ALGORITHM, JWT_EXPIRATION_HOURS,
    API_TOKENS, get_encryption_cipher
)

logger = logging.getLogger("chaxai.security")

security = HTTPBearer(auto_error=False)


class User(BaseModel):
    user_id: str
    tenant_id: str
    email: Optional[str] = None
    is_admin: bool = False
    permissions: List[str] = []


class TokenData(BaseModel):
    user_id: str
    tenant_id: str
    exp: datetime


def create_access_token(user: User) -> str:
    """Create a JWT access token."""
    expire = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    
    payload = {
        "sub": user.user_id,
        "tenant_id": user.tenant_id,
        "email": user.email,
        "is_admin": user.is_admin,
        "permissions": user.permissions,
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    }
    
    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return token


def verify_token(token: str) -> Optional[User]:
    """Verify and decode a JWT token."""
    try:
        payload = jwt.decode(
            token,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM]
        )
        
        user = User(
            user_id=payload["sub"],
            tenant_id=payload["tenant_id"],
            email=payload.get("email"),
            is_admin=payload.get("is_admin", False),
            permissions=payload.get("permissions", [])
        )
        
        return user
        
    except jwt.ExpiredSignatureError:
        logger.warning("Token expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token: {e}")
        return None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """Get current user from JWT token or API key."""
    
    if not credentials:
        # Check for API token
        from fastapi import Request
        from starlette.requests import Request as StarletteRequest
        
        # This is a simplified check - in production, inject Request properly
        api_token = None  # Get from request headers
        
        if api_token and api_token in API_TOKENS:
            # API token authentication
            return User(
                user_id="api_user",
                tenant_id="default",
                is_admin=False,
                permissions=["read", "write"]
            )
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # JWT authentication
    user = verify_token(credentials.credentials)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return bcrypt.checkpw(
        plain_password.encode('utf-8'),
        hashed_password.encode('utf-8')
    )


def encrypt_sensitive_data(data: str) -> str:
    """Encrypt sensitive data."""
    cipher = get_encryption_cipher()
    encrypted = cipher.encrypt(data.encode())
    return encrypted.decode()


def decrypt_sensitive_data(encrypted_data: str) -> str:
    """Decrypt sensitive data."""
    cipher = get_encryption_cipher()
    decrypted = cipher.decrypt(encrypted_data.encode())
    return decrypted.decode()


class PermissionChecker:
    """Check user permissions."""
    
    def __init__(self, required_permissions: List[str]):
        self.required_permissions = required_permissions
    
    def __call__(self, user: User = Depends(get_current_user)) -> User:
        for permission in self.required_permissions:
            if permission not in user.permissions:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission '{permission}' required"
                )
        return user


# Permission dependencies
require_admin = PermissionChecker(["admin"])
require_write = PermissionChecker(["write"])
require_read = PermissionChecker(["read"])
