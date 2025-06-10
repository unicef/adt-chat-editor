from fastapi import APIRouter

from src.structs import PublishMetadata, PublishRequest, PublishResponse
from src.settings import custom_logger


# Create logger
logger = custom_logger("Publish API Router")


# Create router
router = APIRouter(prefix="/publish", tags=["Publish"])


# Define the endpoints
@router.post("", response_model=PublishResponse)
async def publish_changes(request: PublishRequest):
    """Publish the changes generated for an ADT (GitHub PR)."""
    logger.debug(f"Publishing changes: request={request}")
    # TODO: Implement publishing logic
    return PublishResponse(
        status="published",
        metadata=PublishMetadata(id="", title="", changes=[]),
    )
