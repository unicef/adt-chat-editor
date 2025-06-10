import os
import sys

sys.path.append(os.getcwd())


from fastapi import APIRouter

from src.core.state_loader import StateCheckpointManager
from src.structs import ChatEditRequest, ChatEditResponse, ChatMessageResponse
from src.settings import custom_logger, STATE_CHECKPOINTS_DIR
from src.utils.messages import message_is_agent, message_is_human
from src.workflows.graph import graph


# Create logger and state loader
logger = custom_logger("Chat API Router")
state_checkpoint_manager = StateCheckpointManager()


# Create router
router = APIRouter(prefix="/chat", tags=["Chat"])


# Define the endpoints
@router.post("/edit", response_model=ChatEditResponse)
async def chat_edit(request: ChatEditRequest) -> ChatEditResponse:
    """Make changes on the current version of the ADT using natural language."""
    logger.debug(
        f"Chat edit request: session_id={request.session_id}, language={request.language}"
    )
    logger.debug(f"Listdir: {os.listdir(STATE_CHECKPOINTS_DIR)}")

    # Get project root directory
    checkpoint_path = os.path.join(STATE_CHECKPOINTS_DIR, request.session_id)
    logger.debug(f"Checkpoint path: {checkpoint_path}")

    if os.path.exists(checkpoint_path):
        state_checkpoint = state_checkpoint_manager.load_state_checkpoint(
            request, path=os.path.join(checkpoint_path, "checkpoint.json")
        )
        logger.debug(f"Loaded state checkpoint: {state_checkpoint}")
    else:
        state_checkpoint = state_checkpoint_manager.create_new_state_checkpoint(
            request, path=checkpoint_path
        )
        logger.debug(f"Created new state checkpoint: {state_checkpoint}")

    logger.debug(f"Invoking graph with state: {state_checkpoint}")
    output = await graph.ainvoke(state_checkpoint)

    # Format messages
    messages = [
        ChatMessageResponse(
            message_number=k,
            content=message.content,
            is_agent=message_is_agent(message),
            show=message_is_human(message),
        )
        for k, message in enumerate(output["messages"])
    ]

    # Create response
    response = ChatEditResponse(
        session_id=request.session_id,
        messages=messages,
        book_information=request.book_information,
    )

    # Save state checkpoint
    state_checkpoint_manager.save_state_checkpoint(request, output)

    return response
