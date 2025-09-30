"""JWT authentication middleware for FastAPI."""

from typing import Optional

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from src.utils.auth import verify_jwt_token


class JWTMiddleware(BaseHTTPMiddleware):
    """Middleware to check JWT tokens on protected routes."""

    def __init__(self, app, exclude_paths: Optional[list] = None):
        """
        Initialize the JWT middleware.

        Args:
            app: The FastAPI application
            exclude_paths: List of paths to exclude from JWT verification
        """
        super().__init__(app)
        self.exclude_paths = exclude_paths or [
            "/docs",
            "/redoc",
            "/openapi.json",
            "/health",
            "/assets",
            "/input",
            "/output",
        ]

    async def dispatch(self, request: Request, call_next):
        """Process the request and check for JWT token if required."""
        # Check if the path should be excluded from JWT verification
        path = request.url.path

        # Skip JWT check for excluded paths or static files
        if any(path.startswith(excluded) for excluded in self.exclude_paths):
            return await call_next(request)

        # Extract token from Authorization header or query parameter
        token = None
        authorization: Optional[str] = request.headers.get("Authorization")

        if authorization:
            # Check if it's a Bearer token
            try:
                scheme, token = authorization.split()
                if scheme.lower() != "bearer":
                    raise ValueError("Invalid scheme")
            except ValueError:
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={
                        "detail": "Invalid authorization header format. Expected 'Bearer <token>'"
                    },
                    headers={"WWW-Authenticate": "Bearer"},
                )
        else:
            # Try to get token from query parameter
            token = request.query_params.get("token")

        if not token:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "detail": "Authorization token missing. Provide via 'Authorization: Bearer <token>' header or '?token=<token>' query parameter"
                },
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Verify the token
        try:
            verify_jwt_token(token)
            # Token is valid, no need to store user info since there are no users
        except HTTPException as jwt_exc:
            # Return the JWT-related HTTP exception response directly
            return JSONResponse(
                status_code=jwt_exc.status_code,
                content={"detail": jwt_exc.detail},
                headers=jwt_exc.headers or {},
            )
        except Exception:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Token verification failed"},
                headers={"WWW-Authenticate": "Bearer"},
            )

        response = await call_next(request)
        return response
