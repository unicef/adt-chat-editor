import subprocess
import os
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
from src.settings import custom_logger

# Create logger
logger = custom_logger("ADT Utils API Router")

# Create router
router = APIRouter(prefix="/adt-utils", tags=["ADT Utils"])

class RunAllRequest(BaseModel):
    target_dir: str
    start: int
    end: int

class RunAllResponse(BaseModel):
    status: str
    message: str
    output: Optional[str] = None
    error: Optional[str] = None

@router.post("/run-all")
async def run_all(request: RunAllRequest):
    """Endpoint to run the make run-all command with specified parameters."""
    try:
        # Validate input parameters
        if request.start < 0 or request.end < 0:
            raise HTTPException(status_code=400, detail="START and END values must be non-negative")
        
        if request.start > request.end:
            raise HTTPException(status_code=400, detail="START value must be less than or equal to END value")
        
        # Change to the adt-utils directory
        adt_utils_dir = "data/adt-utils"
        if not os.path.exists(adt_utils_dir):
            raise HTTPException(status_code=404, detail=f"Directory {adt_utils_dir} not found")
        
        # Prepare the command
        command = [
            "python", 
            "standardize_all.py",
            f"{request.start}",
            f"{request.end}",
            "--output-dir",
            f"{request.target_dir}",
        ]

        logger.info(f"Executing command: {' '.join(command)} in directory: {adt_utils_dir}")
        
        # Execute the command
        result = subprocess.run(
            command,
            cwd=adt_utils_dir,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode == 0:
            logger.info("Command executed successfully")
            return RunAllResponse(
                status="success",
                message="Command executed successfully",
                output=result.stdout
            )
        else:
            logger.error(f"Command failed with return code {result.returncode}")
            return RunAllResponse(
                status="error",
                message=f"Command failed with return code {result.returncode}",
                error=result.stderr
            )
            
    except subprocess.TimeoutExpired:
        logger.error("Command execution timed out")
        raise HTTPException(status_code=408, detail="Command execution timed out")
    
    except Exception as e:
        logger.error(f"Error executing command: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/status")
async def check_adt_utils_status():
    """Endpoint to check if adt-utils directory exists and is accessible."""
    adt_utils_dir = "data/adt-utils"
    
    if os.path.exists(adt_utils_dir):
        try:
            # Try to list directory contents to verify accessibility
            contents = os.listdir(adt_utils_dir)
            return {
                "status": "ok",
                "directory": adt_utils_dir,
                "exists": True,
                "accessible": True,
                "files_count": len(contents)
            }
        except PermissionError:
            return {
                "status": "error",
                "directory": adt_utils_dir,
                "exists": True,
                "accessible": False,
                "message": "Directory exists but is not accessible"
            }
    else:
        return {
            "status": "error",
            "directory": adt_utils_dir,
            "exists": False,
            "accessible": False,
            "message": "Directory does not exist"
        }
