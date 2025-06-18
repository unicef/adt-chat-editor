from typing import List
from pydantic import BaseModel

from src.structs.books import BookInformation
from src.structs.status import WorkflowStatus


class ChatMessageResponse(BaseModel):
    """Model representing a message in a chat conversation."""

    message_number: int
    content: str
    is_agent: bool
    show: bool


class ChatEditRequest(BaseModel):
    """Model for chat-based editing requests."""

    session_id: str
    user_message: str
    language: str
    pages: List
    book_information: BookInformation


class ChatEditResponse(BaseModel):
    """Model for chat-based editing responses."""

    session_id: str
    status: WorkflowStatus
    messages: List[ChatMessageResponse]
    book_information: BookInformation
