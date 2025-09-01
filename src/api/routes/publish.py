from typing import Dict, List

from fastapi import APIRouter, Body

from src.core.git_manager_provider import get_git_manager
from src.settings import custom_logger
from src.structs import PublishMetadata, PublishRequest, PublishResponse

# Create logger
logger = custom_logger("Publish API Router")

# Create router
router = APIRouter(prefix="/publish", tags=["Publish"])

# Git manager accessor is provided by core.git_manager_provider


# Save user changes (commit)
@router.post("/commit", response_model=PublishResponse)
async def commit_changes(request: PublishRequest):
    """Commit changes without pushing."""
    logger.debug(f"Committing changes: request={request}")
    try:
        git_manager = get_git_manager()
        if git_manager is None:
            return PublishResponse(
                status="not-committed",
                metadata=PublishMetadata(id=request.book_information.id, title="", changes=[]),
            )
        message = request.message
        committed = await git_manager.commit_changes(message=message)

        if committed:
            logger.debug(f"Committed changes with message: {message}")
            return PublishResponse(
                status="committed",
                metadata=PublishMetadata(id=request.book_information.id, title="", changes=[]),
            )
        else:
            logger.debug("No changes to commit")
            return PublishResponse(
                status="not-committed",
                metadata=PublishMetadata(id=request.book_information.id, title="", changes=[]),
            )

    except Exception as e:
        logger.error(f"Error committing changes: {e}")
        return PublishResponse(status="error", metadata=PublishMetadata(id="", title="", changes=[]))


# List recent system commits on current branch
@router.get("/commits", response_model=List[Dict[str, str]])
async def list_branch_commits():
    try:
        git_manager = get_git_manager()
        if git_manager is None:
            return []
        current_branch = await git_manager.current_branch()
        commits = await git_manager.list_commits(branch_name=current_branch)
        return commits
    except Exception as e:
        logger.debug(f"Error fetching commits: {e}")
        return []


# Checkout a specific commit
@router.post("/checkout-commit")
async def checkout_commit(commit: Dict[str, str] = Body(...)):
    commit_hash = commit.get("hash")
    try:
        git_manager = get_git_manager()
        if git_manager is None:
            return {"status": "error", "detail": "git manager unavailable"}
        await git_manager.checkout_commit(commit_hash)
        return {"status": "ok", "commit": commit_hash}
    except Exception as e:
        logger.debug(f"Error checking out commit: {e}")
        return {"status": "error", "detail": str(e)}


@router.post("", response_model=PublishResponse)
async def publish_changes(request: PublishRequest):
    logger.debug(f"Received publish request: {request}")

    book_information = request.book_information
    message = request.message or f"Commit for {book_information.id}"

    try:
        git_manager = get_git_manager()
        if git_manager is None:
            return PublishResponse(
                status="not-published",
                metadata=PublishMetadata(id=book_information.id, title=message, changes=[]),
            )
        current_branch = await git_manager.current_branch()
        logger.debug(f"Current working branch: {current_branch}")

        previous_commits = await git_manager.list_commits(branch_name=current_branch)
        current_commit = await git_manager.commit_changes(message=message)

        if current_branch == "HEAD":
            current_branch = git_manager.true_branch_name
        
        if current_commit:
            logger.debug(f"Committed changes with message: {message}")

            await git_manager.safe_push(branch_name=current_branch)
            logger.debug(f"Pushed branch '{current_branch}' to origin")

            await git_manager.tag_last_published_commit()
            logger.debug("Tagged last published commit")

            pr_exists = await git_manager.pull_request_exists(branch_name=current_branch)
            if not pr_exists:
                pr_url = await git_manager.create_pull_request(
                    title=f"ADT-chat-editor: {message}",
                    body=message,
                    base="main"
                )
                logger.debug(f"Created new PR: {pr_url}")                
            else:
                logger.debug(f"PR already exists for branch '{current_branch}'")

            return PublishResponse(
                status="published",
                metadata=PublishMetadata(id=book_information.id, title=message, changes=[]),
            )

        elif previous_commits:
            await git_manager.safe_push(branch_name=current_branch)
            logger.debug(f"Pushed branch '{current_branch}' to origin")

            await git_manager.tag_last_published_commit()
            logger.debug("Tagged last published commit")

            pr_exists = await git_manager.pull_request_exists(branch_name=current_branch)
            if not pr_exists:
                pr_url = await git_manager.create_pull_request(
                    title=f"ADT-chat-editor: {message}",
                    body=message,
                    base="main"
                )
                logger.debug(f"Created new PR: {pr_url}")                
            else:
                logger.debug(f"PR already exists for branch '{current_branch}'")

            return PublishResponse(
                status="published",
                metadata=PublishMetadata(id=book_information.id, title=message, changes=[]),
            )

        else:
            logger.debug("No changes to commit and push. Skipping commit/push step.")
            return PublishResponse(
                status="not-published",
                metadata=PublishMetadata(id=book_information.id, title=message, changes=[]),
            )

    except Exception as e:
        logger.error(f"Error publishing changes: {e}")
        return PublishResponse(
            status="error",
            metadata=PublishMetadata(id=book_information.id, title="", changes=[]),
        )
