"""Authentication routes."""

from fastapi import APIRouter, Request
from pydantic import BaseModel
from urllib.parse import urlencode
from src.settings import settings

from src.utils.auth import create_jwt_token


router = APIRouter(prefix="/auth", tags=["Authentication"])


class GenerateLinkResponse(BaseModel):
    """Generate link response model."""

    frontend_url: str
    token: str
    expires_in: int


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
