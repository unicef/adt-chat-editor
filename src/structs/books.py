from typing import List, Optional
from pydantic import BaseModel


class Book(BaseModel):
    """Model representing a book in the system."""

    title: str
    id: str
    cover_image: str  # base64 string
    author: Optional[str] = None
    description: Optional[str] = None


class Chapter(BaseModel):
    """Model representing a chapter in a book."""

    id: str
    title: str


class BookInfo(BaseModel):
    """Model containing static information about a book."""

    title: str
    id: str
    author: Optional[str] = None
    chapters: List[Chapter]


class PageContent(BaseModel):
    """Model representing a page's content in a book."""

    page_id: str
    title: str
    contents: str  # HTML content


class BookContent(BaseModel):
    """Model containing a list of page contents."""

    contents: List[PageContent]


class BookInformation(BaseModel):
    """Model containing basic book identification information."""

    id: str
    version: str
