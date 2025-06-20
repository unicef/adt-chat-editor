from pydantic import BaseModel


class BookInformation(BaseModel):
    """Model containing basic book identification information."""

    id: str
    version: str
