import subprocess
import os
from fastapi import APIRouter, HTTPException, Query
from src.settings import custom_logger, ADT_UTILS_DIR
from src.structs import RunAllRequest, RunAllResponse

# Create logger
logger = custom_logger("ADT Utils API Router")

# Create router
router = APIRouter(prefix="/adt-utils", tags=["ADT Utils"])


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
        if not os.path.exists(ADT_UTILS_DIR):
            raise HTTPException(status_code=404, detail=f"Directory {ADT_UTILS_DIR} not found")
        
        # Prepare the command
        command = [
            "python", 
            "standardize_all.py",
            f"{request.start}",
            f"{request.end}",
            "--output-dir",
            f"{request.target_dir}",
        ]

        logger.info(f"Executing command: {' '.join(command)} in directory: {ADT_UTILS_DIR}")
        
        # Execute the command
        result = subprocess.run(
            command,
            cwd=ADT_UTILS_DIR,
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
    if os.path.exists(ADT_UTILS_DIR):
        try:
            # Try to list directory contents to verify accessibility
            contents = os.listdir(ADT_UTILS_DIR)
            return {
                "status": "ok",
                "directory": ADT_UTILS_DIR,
                "exists": True,
                "accessible": True,
                "files_count": len(contents)
            }
        except PermissionError:
            return {
                "status": "error",
                "directory": ADT_UTILS_DIR,
                "exists": True,
                "accessible": False,
                "message": "Directory exists but is not accessible"
            }
    else:
        return {
            "status": "error",
            "directory": ADT_UTILS_DIR,
            "exists": False,
            "accessible": False,
            "message": "Directory does not exist"
        }
