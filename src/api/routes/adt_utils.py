import subprocess
import os
from enum import Enum
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from src.settings import custom_logger, ADT_UTILS_DIR, OUTPUT_DIR  # Added OUTPUT_DIR import
from src.structs import RunAllRequest, RunAllResponse

# Create logger
logger = custom_logger("ADT Utils API Router")

# Create router
router = APIRouter(prefix="/adt-utils", tags=["ADT Utils"])

class ScriptType(str, Enum):
    VALIDATE_ADT = "validate_adt"
    FIX_MISSING_DATA = "fix_missing_data_ids"
    RESTRUCTURE_TEXT = "restructure_text"

class RunScriptRequest(BaseModel):
    script_type: ScriptType = Field(..., description="Type of script to run")
    start: Optional[int] = Field(None, description="Start value (only for restructure_text)", ge=0)
    end: Optional[int] = Field(None, description="End value (only for restructure_text)", ge=0)
    verbose: bool = Field(True, description="Enable verbose output")

    # Pydantic v2 model config
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "script_type": "restructure_text",
                "start": 10,
                "end": 15,
                "verbose": True,
            }
        }
    )

@router.post("/run-script")
async def run_script(request: RunScriptRequest):
    """Endpoint to run any of the three available scripts with specified parameters."""
    try:
        # Validate input parameters based on script type
        if request.script_type == ScriptType.RESTRUCTURE_TEXT:
            if request.start is None or request.end is None:
                raise HTTPException(
                    status_code=400, 
                    detail="START and END values are required for restructure_text script"
                )
            
            if request.start < 0 or request.end < 0:
                raise HTTPException(
                    status_code=400, 
                    detail="START and END values must be non-negative"
                )
            
            if request.start > request.end:
                raise HTTPException(
                    status_code=400, 
                    detail="START value must be less than or equal to END value"
                )
        
        # Check if directories exist
        if not os.path.exists(ADT_UTILS_DIR):
            raise HTTPException(
                status_code=404, 
                detail=f"Directory {ADT_UTILS_DIR} not found"
            )
        
        if not os.path.exists(OUTPUT_DIR):
            raise HTTPException(
                status_code=404, 
                detail=f"Output directory {OUTPUT_DIR} not found"
            )
        
        # Convert OUTPUT_DIR to absolute path to avoid relative path issues
        # when running from ADT_UTILS_DIR
        abs_output_dir = os.path.abspath(OUTPUT_DIR)
        
        # Build command based on script type
        command = ["python"]
        
        if request.script_type == ScriptType.VALIDATE_ADT:
            command.extend([
                "validate_adt.py",
                abs_output_dir  # Using absolute path to avoid relative path issues
            ])
            if request.verbose:
                command.append("--verbose")
                
        elif request.script_type == ScriptType.FIX_MISSING_DATA:
            command.extend([
                "fix_missing_data_ids.py",
                abs_output_dir  # Using absolute path to avoid relative path issues
            ])
            if request.verbose:
                command.append("--verbose")
                
        elif request.script_type == ScriptType.RESTRUCTURE_TEXT:
            command.extend([
                "restructure_text.py",
                str(request.start),
                str(request.end),
                "--output-dir",
                abs_output_dir  # Using absolute path to avoid relative path issues
            ])
            # Note: restructure_text.py might not support --verbose flag
        
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
            logger.info(f"Script {request.script_type.value} executed successfully")
            return RunAllResponse(
                status="success",
                message=f"Script {request.script_type.value} executed successfully",
                output=result.stdout
            )
        elif result.returncode == 1 and request.script_type == ScriptType.VALIDATE_ADT:
            # For validation scripts, return code 1 typically means "found issues" not "failed"
            logger.info(f"Script {request.script_type.value} completed - found validation issues")
            return RunAllResponse(
                status="success",
                message=f"Script {request.script_type.value} completed - found validation issues",
                output=result.stdout
            )
        else:
            # Log both stdout and stderr for debugging
            logger.error(f"Script {request.script_type.value} failed with return code {result.returncode}")
            logger.error(f"STDERR: {result.stderr}")
            logger.error(f"STDOUT: {result.stdout}")
            
            # Include both stdout and stderr in the error response
            error_details = f"Return code: {result.returncode}\n"
            if result.stderr:
                error_details += f"STDERR: {result.stderr}\n"
            if result.stdout:
                error_details += f"STDOUT: {result.stdout}"
            
            return RunAllResponse(
                status="error",
                message=f"Script {request.script_type.value} failed with return code {result.returncode}",
                error=error_details
            )
            
    except subprocess.TimeoutExpired:
        logger.error(f"Script {request.script_type.value} execution timed out")
        raise HTTPException(status_code=408, detail="Script execution timed out")
    
    except Exception as e:
        logger.error(f"Error executing script {getattr(request, 'script_type', 'unknown')}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/scripts/info")
async def get_scripts_info():
    """Endpoint to get information about available scripts and their parameters."""
    return {
        "available_scripts": {
            "validate_adt": {
                "description": "Validate ADT files in the output directory",
                "parameters": ["verbose (optional)"],
                "example": {
                    "script_type": "validate_adt",
                    "verbose": True
                }
            },
            "fix_missing_data_ids": {
                "description": "Fix missing data IDs in the target directory",
                "parameters": ["verbose (optional)"],
                "example": {
                    "script_type": "fix_missing_data_ids",
                    "verbose": True
                }
            },
            "restructure_text": {
                "description": "Restructure text files with start and end range",
                "parameters": ["start (required)", "end (required)", "verbose (optional)"],
                "example": {
                    "script_type": "restructure_text",
                    "start": 10,
                    "end": 15,
                    "verbose": True
                }
            }
        },
        "static_paths": {
            "folder_path": OUTPUT_DIR,
            "target_dir": OUTPUT_DIR,
            "output_dir": OUTPUT_DIR
        }
    }

# Keep the original endpoint for backward compatibility
@router.post("/run-all")
async def run_all(request: RunAllRequest):
    """Legacy endpoint - redirects to restructure_text script for backward compatibility."""
    try:
        # Convert to new format and call the restructure_text script directly
        # Validate input parameters (same as original)
        if request.start < 0 or request.end < 0:
            raise HTTPException(status_code=400, detail="START and END values must be non-negative")
        
        if request.start > request.end:
            raise HTTPException(status_code=400, detail="START value must be less than or equal to END value")
        
        # Create new request format
        new_request = RunScriptRequest(
            script_type=ScriptType.RESTRUCTURE_TEXT,
            start=request.start,
            end=request.end,
            verbose=True
        )
        
        # Call the new endpoint
        return await run_script(new_request)
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Error in legacy run-all endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/status")
async def check_adt_utils_status():
    """Endpoint to check if adt-utils directory exists and is accessible."""    
    status_info = {
        "adt_utils_dir": {
            "path": ADT_UTILS_DIR,
            "exists": False,
            "accessible": False
        },
        "output_dir": {
            "path": OUTPUT_DIR,
            "exists": False,
            "accessible": False
        }
    }
    
    # Check ADT_UTILS_DIR
    if os.path.exists(ADT_UTILS_DIR):
        status_info["adt_utils_dir"]["exists"] = True
        try:
            contents = os.listdir(ADT_UTILS_DIR)
            status_info["adt_utils_dir"]["accessible"] = True
            status_info["adt_utils_dir"]["files_count"] = len(contents)
        except PermissionError:
            status_info["adt_utils_dir"]["accessible"] = False
            status_info["adt_utils_dir"]["message"] = "Directory exists but is not accessible"
    else:
        status_info["adt_utils_dir"]["message"] = "Directory does not exist"
    
    # Check OUTPUT_DIR
    if os.path.exists(OUTPUT_DIR):
        status_info["output_dir"]["exists"] = True
        try:
            contents = os.listdir(OUTPUT_DIR)
            status_info["output_dir"]["accessible"] = True
            status_info["output_dir"]["files_count"] = len(contents)
        except PermissionError:
            status_info["output_dir"]["accessible"] = False
            status_info["output_dir"]["message"] = "Directory exists but is not accessible"
    else:
        status_info["output_dir"]["message"] = "Directory does not exist"
    
    # Determine overall status
    overall_status = "ok" if (
        status_info["adt_utils_dir"]["exists"] and 
        status_info["adt_utils_dir"]["accessible"] and
        status_info["output_dir"]["exists"] and 
        status_info["output_dir"]["accessible"]
    ) else "error"
    
    return {
        "status": overall_status,
        **status_info
    }
