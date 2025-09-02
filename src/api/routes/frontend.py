"""Frontend static file serving endpoints."""

from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, HTMLResponse

from src.settings import custom_logger

# Create the logger
logger = custom_logger("Frontend Router")

# Create router
router = APIRouter(
    tags=["Frontend"],
)


@router.get("/", response_class=HTMLResponse)
async def read_root():
    """Serve the frontend's index.html file."""
    index_file = Path("frontend/index.html")
    if index_file.exists():
        return FileResponse(index_file)
    raise HTTPException(status_code=404, detail="index.html not found")
