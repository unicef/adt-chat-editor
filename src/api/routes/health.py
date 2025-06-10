from fastapi import APIRouter

from src.settings import custom_logger


# Create logger
logger = custom_logger("Health API Router")

# Create router
router = APIRouter(prefix="/health", tags=["Health"])


# Define the endpoints
@router.get("")
async def health():
    """Endpoint to check if the service is up and running."""
    return {"status": "ok"}
