from fastapi import APIRouter, HTTPException
from typing import List
from src.structs.terminal import ExecuteCommandRequest, CommandResponse, CommandHistory
from src.utils.terminal_service import TerminalService

router = APIRouter(prefix="/terminal", tags=["terminal"])

# Global terminal service instance
_terminal_service = TerminalService()


@router.post("/execute", response_model=CommandResponse)
async def execute_command(request: ExecuteCommandRequest):
    """Execute a command in the backend container"""
    try:
        return _terminal_service.execute_command(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/history", response_model=List[CommandHistory])
async def get_command_history():
    """Get command execution history"""
    try:
        return _terminal_service.get_history()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get history: {str(e)}")


@router.delete("/history")
async def clear_command_history():
    """Clear command execution history"""
    try:
        _terminal_service.clear_history()
        return {"message": "History cleared successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to clear history: {str(e)}"
        )
