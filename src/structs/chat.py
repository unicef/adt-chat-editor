from typing import List
from pydantic import BaseModel

from src.structs.books import BookInformation


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
    book_information: BookInformation


class ChatEditResponse(BaseModel):
    """Model for chat-based editing responses."""

    session_id: str
    messages: List[ChatMessageResponse]
    book_information: BookInformation
