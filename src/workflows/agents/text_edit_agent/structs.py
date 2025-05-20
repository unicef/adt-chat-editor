from pydantic import BaseModel


class TextEditRequest(BaseModel):
    """Request for text editing."""

    text: str
    instruction: (
        str  # Simple instruction like "make it shorter" or "make it more engaging"
    )


class TextEditResponse(BaseModel):
    """Response from the text editing model."""

    edited_text: str
