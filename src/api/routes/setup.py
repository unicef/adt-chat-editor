"""Setup endpoints to initialize languages, Tailwind, and caches."""

import os
import subprocess
from typing import Dict

from fastapi import APIRouter, HTTPException

from src.utils.initialization import (
    initialize_languages,
    initialize_tailwind,
    initialize_translated_html_content,
)

# Setup router
router = APIRouter(prefix="/setup", tags=["setup"])


# Endpoints
@router.post("/initialize")
async def install_npm_packages() -> Dict[str, str | list[str]]:
    """Install npm packages in the /app/data/output directory."""
    try:
        # Initialize languages
        languages = await initialize_languages()

        # Initialize tailwind
        tailwind_status = await initialize_tailwind()

        # Initialize translated HTML contents
        translated_html_statuses = []
        for language in languages:
            translated_html_status = await initialize_translated_html_content(language)
            translated_html_statuses.append(translated_html_status.value)

        return {
            "status": "Initialization successful!",
            "languages": languages,
            "tailwind_status": tailwind_status.value,
            "translated_html_statuses": translated_html_statuses,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to start npm installation: {str(e)}"
        )


@router.get("/npm-status")
async def check_npm_status() -> Dict[str, str]:
    """Check the status of npm packages in the /app/data/output directory."""
    try:
        # Check if node_modules exists
        if not os.path.exists("/app/data/output/node_modules"):
            return {
                "status": "not_installed",
                "message": "node_modules directory not found",
            }

        # Run npm list to check installed packages
        result = subprocess.run(
            "cd /app/data/output && npm list --json",
            shell=True,
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            return {"status": "installed", "message": "npm packages are installed"}
        else:
            return {
                "status": "error",
                "message": f"Error checking npm packages: {result.stderr}",
            }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to check npm status: {str(e)}"
        )
