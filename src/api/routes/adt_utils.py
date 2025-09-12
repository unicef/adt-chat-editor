"""Endpoints to run ADT utility scripts from the backend."""

import os
import subprocess
import sys
from copy import deepcopy
from enum import Enum
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field

# Cache for ADT utils imports
_adt_utils_imports = None

def _get_adt_utils():
    """Lazily load ADT utils imports."""
    global _adt_utils_imports
    
    if _adt_utils_imports is not None:
        return _adt_utils_imports
    
    # Add data/adt-utils/src to Python path for imports
    # Try different possible paths for local dev vs Docker
    possible_paths = [
        Path(__file__).parent.parent.parent / "data" / "adt-utils" / "src",  # Local dev
        Path("/app/data/adt-utils/src"),  # Docker container
        Path(__file__).resolve().parent.parent.parent / "data" / "adt-utils" / "src",  # Absolute path
    ]

    adt_utils_src = None
    for path in possible_paths:
        if path.exists():
            adt_utils_src = str(path)
            if adt_utils_src not in sys.path:
                sys.path.insert(0, adt_utils_src)
            break

    if adt_utils_src is None:
        raise ImportError("Could not find data/adt-utils/src directory")

    from script_registry import PRODUCTION_SCRIPTS
    from structs.script import (
        Script,
        ScriptCategory,
        ScriptArgument,
        ScriptExample,
    )
    
    _adt_utils_imports = {
        'PRODUCTION_SCRIPTS': PRODUCTION_SCRIPTS,
        'Script': Script,
        'ScriptCategory': ScriptCategory,
        'ScriptArgument': ScriptArgument,
        'ScriptExample': ScriptExample,
    }
    
    return _adt_utils_imports
from src.settings import ADT_UTILS_DIR, OUTPUT_DIR, custom_logger
from src.structs import RunAllRequest, RunAllResponse

# Create logger
logger = custom_logger("ADT Utils API Router")

# Create router
router = APIRouter(prefix="/adt-utils", tags=["ADT Utils"])


class RunScriptRequest(BaseModel):
    """Request model to execute a script with optional parameters."""

    script_id: str = Field(..., description="ID of the script to run")
    start_page: Optional[int] = Field(
        None, description="Start value (only for restructure_text)", ge=0
    )
    end_page: Optional[int] = Field(
        None, description="End value (only for restructure_text)", ge=0
    )
    verbose: bool = Field(True, description="Enable verbose output")

    # Pydantic v2 model config
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "script_type": "restructure_text",
                "start_page": 10,
                "end_page": 15,
                "verbose": True,
            }
        }
    )


@router.post("/run-script")
async def run_script(request: RunScriptRequest):
    """Endpoint to run any of the three available scripts with specified parameters."""
    try:
        # Find the script to run
        adt_utils = _get_adt_utils()
        script_to_run = None
        for script in adt_utils['PRODUCTION_SCRIPTS']:
            if script.id == request.script_id:
                script_to_run = script.model_copy(deep=True)
                break
        if script_to_run is None:
            raise HTTPException(
                status_code=404, detail=f"Script with ID {request.script_id} not found"
            )

        # Check if directories exist
        if not os.path.exists(ADT_UTILS_DIR):
            raise HTTPException(
                status_code=404, detail=f"Directory {ADT_UTILS_DIR} not found"
            )

        if not os.path.exists(OUTPUT_DIR):
            raise HTTPException(
                status_code=404, detail=f"Output directory {OUTPUT_DIR} not found"
            )

        # Gather the replaced values
        for arg in script_to_run.arguments:
            if arg.name == "start_page" and request.start_page is not None:
                arg.default = request.start_page
            elif arg.name == "end_page" and request.end_page is not None:
                arg.default = request.end_page
            elif arg.name == "verbose" and request.verbose is not None:
                arg.default = request.verbose

        # Absolute path to the output directory
        abs_output_dir = os.path.abspath(OUTPUT_DIR)

        # Build command based on script
        command = ["python"]

        # Add the target directory to the command
        command.extend([script_to_run.path, abs_output_dir])

        # Add the script arguments to the command
        for arg in script_to_run.arguments:
            if arg.name == "target_dir":
                continue
            elif (arg.name == "start_page" or arg.name == "end_page") and (
                arg.default in [None, -1]
            ):
                continue
            elif arg.default is None:
                continue
            elif (arg.type == "bool") and (arg.default == False):
                continue
            elif (arg.type == "bool") and (arg.default == True):
                command.extend(["--" + arg.name])
            else:
                command.extend(["--" + arg.name, str(arg.default)])

        logger.info(
            f"Executing command: {' '.join(command)} in directory: {ADT_UTILS_DIR}"
        )

        # Execute the command
        result = subprocess.run(
            command,
            cwd=ADT_UTILS_DIR,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout
        )

        if result.returncode == 0:
            logger.info(f"Script {script_to_run.id} executed successfully")
            return RunAllResponse(
                status="success",
                message=f"Script {script_to_run.id} executed successfully",
                output=result.stdout,
            )
        elif result.returncode == 1 and script_to_run.id == "validate_adt":
            # For validation scripts, return code 1 typically means "found issues" not "failed"
            logger.info(
                f"Script {request.script_id} completed - found validation issues"
            )
            return RunAllResponse(
                status="success",
                message=f"Script {request.script_id} completed - found validation issues",
                output=result.stdout,
            )
        else:
            # Log both stdout and stderr for debugging
            logger.error(
                f"Script {request.script_id} failed with return code {result.returncode}"
            )
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
                message=f"Script {request.script_id} failed with return code {result.returncode}",
                error=error_details,
            )

    except subprocess.TimeoutExpired:
        logger.error(f"Script {request.script_id} execution timed out")
        raise HTTPException(status_code=408, detail="Script execution timed out")

    except Exception as e:
        logger.error(
            f"Error executing script {getattr(request, 'script_id', 'unknown')}: {str(e)}"
        )
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/scripts/info")
async def get_scripts_info():
    """Endpoint to get information about available scripts and their parameters."""
    adt_utils = _get_adt_utils()
    return {
        "available_scripts": [
            {
                "id": script.id,
                "description": script.description,
                "parameters": [arg.name for arg in script.arguments],
                "example": {"script_id": script.id, "verbose": True},
            }
            for script in adt_utils['PRODUCTION_SCRIPTS']
        ]
    }


@router.get("/status")
async def check_adt_utils_status():
    """Endpoint to check if adt-utils directory exists and is accessible."""
    status_info = {
        "adt_utils_dir": {"path": ADT_UTILS_DIR, "exists": False, "accessible": False},
        "output_dir": {"path": OUTPUT_DIR, "exists": False, "accessible": False},
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
            status_info["adt_utils_dir"][
                "message"
            ] = "Directory exists but is not accessible"
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
            status_info["output_dir"][
                "message"
            ] = "Directory exists but is not accessible"
    else:
        status_info["output_dir"]["message"] = "Directory does not exist"

    # Determine overall status
    overall_status = (
        "ok"
        if (
            status_info["adt_utils_dir"]["exists"]
            and status_info["adt_utils_dir"]["accessible"]
            and status_info["output_dir"]["exists"]
            and status_info["output_dir"]["accessible"]
        )
        else "error"
    )

    return {"status": overall_status, **status_info}
