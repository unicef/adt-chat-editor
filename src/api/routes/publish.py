import asyncio
import uuid

from fastapi import APIRouter

from src.structs import PublishMetadata, PublishRequest, PublishResponse
from src.settings import (
    custom_logger, 
    OUTPUT_DIR,
    BASE_BRANCH_NAME
)
from src.core.git_version_manager import AsyncGitVersionManager

# Create logger
logger = custom_logger("Publish API Router")

# Create router
router = APIRouter(prefix="/publish", tags=["Publish"])

# create Git Version Manager
git_manager = AsyncGitVersionManager(OUTPUT_DIR)


# Define the endpoints
@router.post("", response_model=PublishResponse)
async def publish_changes(request: PublishRequest):
    """Publish the changes generated for an ADT (GitHub PR)."""
    logger.debug(f"Publishing changes: request={request}")

    book_information = request.book_information
    message = f"commit_{book_information.id}_{book_information.version}"

    try:
        current_branch = await git_manager.current_branch()
    
        if BASE_BRANCH_NAME not in current_branch:
            uu_id = uuid.uuid4().hex
            current_branch = BASE_BRANCH_NAME + uu_id
    
            await git_manager.create_branch(branch_name=current_branch)
            await git_manager.commit_changes(message=message)
            await git_manager.push_branch(branch_name=current_branch)
            await git_manager.create_pull_request(
                title=f"ADT-chat-editor: {uu_id}",
                body=message, 
                base="main"
            )
        else:
            await git_manager.commit_changes(message=message)
            await git_manager.push_branch(branch_name=current_branch)
    except Exception as e:
        logger.debug(f"Error Publishing changes: {e}")

    return PublishResponse(
        status="published",
        metadata=PublishMetadata(id="", title="", changes=[]),
    )
