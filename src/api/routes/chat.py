from fastapi import APIRouter

from src.structs import ChatEditRequest, ChatEditResponse, ChatMessageResponse
from src.settings import custom_logger


# Create logger
logger = custom_logger("Chat API Router")


# Create router
router = APIRouter(prefix="/chat", tags=["Chat"])


# Define the endpoints
@router.post("/edit", response_model=ChatEditResponse)
async def chat_edit(request: ChatEditRequest):
    """Make changes on the current version of the ADT using natural language."""
    logger.debug(
        f"Chat edit request: session_id={request.session_id}, language={request.language}"
    )

    # TODO: Implement chat-based editing logic
    messages = [
        ChatMessageResponse(
            message_number=1,
            content=request.user_message,
            is_agent=False,
            show=True,
        ),
        ChatMessageResponse(
            message_number=2,
            content="I'll help you make those changes. Let me process your request.",
            is_agent=True,
            show=True,
        ),
        ChatMessageResponse(
            message_number=3,
            content="I'll help you make those changes. Let me process your request.",
            is_agent=True,
            show=True,
        ),
        ChatMessageResponse(
            message_number=4,
            content="Don't show this message to the user.",
            is_agent=True,
            show=False,
        ),
    ]

    return ChatEditResponse(
        session_id=request.session_id,
        messages=messages,
        book_information=request.book_information,
    )
