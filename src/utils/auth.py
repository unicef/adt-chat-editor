"""JWT authentication utilities."""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import jwt
from fastapi import HTTPException, status

from src.settings import settings


def create_jwt_token(
    subject: str = "api_access", additional_claims: Optional[Dict[str, Any]] = None
) -> str:
    """
    Create a JWT token.

    Args:
        subject: The token subject (defaults to "api_access")
        additional_claims: Optional additional claims to include in the token

    Returns:
        The encoded JWT token string
    """
    now = datetime.now(timezone.utc)
    expire = now + timedelta(hours=settings.JWT_EXPIRATION_HOURS)

    payload = {
        "sub": subject,
        "exp": expire,
        "iat": now,
    }

    if additional_claims:
        payload.update(additional_claims)

    return jwt.encode(
        payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )


def verify_jwt_token(token: str) -> Dict[str, Any]:
    """
    Verify and decode a JWT token.

    Args:
        token: The JWT token to verify

    Returns:
        The decoded token payload

    Raises:
        HTTPException: If the token is invalid or expired
    """
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    """
    Extract the subject from a JWT token.

    Args:
        token: The JWT token

    Returns:
        The subject from the token
    """
    payload = verify_jwt_token(token)
    subject = payload.get("sub")
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing subject",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return subject
