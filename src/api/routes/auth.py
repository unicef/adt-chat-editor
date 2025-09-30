"""Authentication routes."""

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel
from urllib.parse import urlencode
from src.settings import settings

from src.utils.auth import create_jwt_token


router = APIRouter(prefix="/auth", tags=["Authentication"])


class LoginRequest(BaseModel):
    """Admin login request model."""
    username: str
    password: str


class LoginResponse(BaseModel):
    """Login response model."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class GenerateLinkResponse(BaseModel):
    """Generate link response model."""

    frontend_url: str
    token: str
    expires_in: int


@router.post("/login", response_model=LoginResponse)
async def admin_login(login_data: LoginRequest):
    """
    Admin login endpoint.

    Authenticates admin users with hardcoded credentials and returns a JWT token.
    """
    # Validate credentials against settings
    if login_data.username != settings.ADMIN_USERNAME or login_data.password != settings.ADMIN_PASSWORD:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create JWT token for admin
    token = create_jwt_token(subject="admin")
    expires_in = settings.JWT_EXPIRATION_HOURS * 3600  # Convert hours to seconds

    return LoginResponse(
        access_token=token,
        expires_in=expires_in
    )


@router.post("/generate-link", response_model=GenerateLinkResponse)
async def generate_frontend_link(request: Request):
    """
    Generate a frontend link with JWT token embedded as URL parameter.

    This creates a JWT token and returns a frontend URL with the token
    included as a query parameter.
    """
    # Create JWT token with generic subject
    token = create_jwt_token(subject="api_access")
    expires_in = settings.JWT_EXPIRATION_HOURS * 3600  # Convert hours to seconds

    # Get the base URL from the request
    base_url = "https://unicef.demos.marvik.cloud/"

    # Create query parameters
    query_params = {"token": token}
    query_string = urlencode(query_params)

    # Construct the frontend URL with token
    frontend_url = f"{base_url}?{query_string}"

    return GenerateLinkResponse(
        frontend_url=frontend_url, token=token, expires_in=expires_in
    )
