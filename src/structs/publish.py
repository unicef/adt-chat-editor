from typing import List
from pydantic import BaseModel

from src.structs.books import BookInformation


class PublishMetadata(BaseModel):
    """Model containing metadata about a published change."""

    id: str
    title: str
    changes: List[str]


class PublishRequest(BaseModel):
    """Model for publishing requests."""

    book_information: BookInformation


class PublishResponse(BaseModel):
    """Model for publishing responses."""

    status: str
    metadata: PublishMetadata
