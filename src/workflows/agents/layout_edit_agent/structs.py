from pydantic import BaseModel


class LayoutEditRequest(BaseModel):
    """Request for layout editing."""

    text: str
    instruction: (
        str  # Simple instruction like "make the title bigger or bold" or "center all the text in the file"
    )


class LayoutEditResponse(BaseModel):
    """Response from the layout editing model."""

    edited_text: str
