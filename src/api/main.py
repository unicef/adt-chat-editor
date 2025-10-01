"""FastAPI application factory and setup."""

import asyncio
import os
import shutil
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi_pagination import add_pagination
from starlette.responses import FileResponse
from starlette.staticfiles import StaticFiles

from src.api.middleware import JWTMiddleware
from src.api.routes import router
from src.settings import (
    ADT_UTILS_DIR,
    BASE_BRANCH_NAME,
    OUTPUT_DIR,
    STATE_CHECKPOINTS_DIR,
    custom_logger,
)

# Create the logger
logger = custom_logger(__name__)


# NoCache STATICFIELD
class NoCacheStaticFiles(StaticFiles):
    """StaticFiles with headers set to disable caching."""

    async def get_response(self, path, scope):
        """Return a response with cache-busting headers."""
        response: FileResponse = await super().get_response(path, scope)
        response.headers["Cache-Control"] = (
            "no-store, no-cache, must-revalidate, max-age=0"
        )
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response


# Create the app
def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    logger.info("Creating FastAPI app")

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # Startup: initialize Git working branch if repo is present
        try:
            from src.core.git_version_manager import AsyncGitVersionManager

            git_dir = os.path.join(OUTPUT_DIR, ".git")
            if os.path.isdir(git_dir):
                manager = await AsyncGitVersionManager.create(
                    repo_path=OUTPUT_DIR,
                    base_branch_name=BASE_BRANCH_NAME,
                    init_working_branch=True,
                )
                # Share the initialized manager with the rest of the app
                from src.core.git_manager_provider import set_git_manager

                set_git_manager(manager)
                logger.info("Git manager initialization scheduled on startup")
            else:
                logger.debug(
                    f"Skipping Git manager initialization: no git repo at {OUTPUT_DIR}"
                )
        except Exception as e:  # pragma: no cover - environment dependent
            logger.debug(f"Git manager initialization skipped: {e}")

        # Schedule ADT utils startup scripts (fix missing data-ids, then regenerate TTS)
        # to run in the background so API startup is not blocked.
        try:
            import json
            import subprocess

            logger.info(
                "Scheduling startup scripts: fix missing data-ids, then TTS regeneration"
            )

            def _run_startup_scripts_sync():
                # Run fixer in isolated subprocess to avoid package name collisions
                fix_runner = os.path.join(
                    os.getcwd(), "src", "api", "startup_fix_and_collect.py"
                )
                try:
                    fix_proc = subprocess.run(
                        [
                            "python",
                            fix_runner,
                            os.path.abspath(OUTPUT_DIR),
                            os.path.abspath(ADT_UTILS_DIR),
                        ],
                        capture_output=True,
                        text=True,
                        timeout=600,
                    )
                except Exception as run_err:
                    logger.error(f"Failed to execute fixer subprocess: {run_err}")
                    fix_proc = None

                added = {}
                if fix_proc and fix_proc.returncode == 0:
                    try:
                        payload = json.loads(fix_proc.stdout or "{}")
                        meta = payload.get("metadata", {}) or {}
                        added = meta.get("added_translations", {}) or {}
                        logger.info(
                            f"Fixer (background) result: success={payload.get('success')}, metadata_keys={list(meta.keys())}"
                        )
                    except Exception as parse_err:
                        logger.error(f"Failed parsing fixer output: {parse_err}")
                else:
                    if fix_proc is not None:
                        logger.error(
                            f"Fixer subprocess failed (code {fix_proc.returncode if fix_proc else 'n/a'})"
                        )
                        if fix_proc.stderr:
                            logger.error(f"Fixer STDERR: {fix_proc.stderr}")
                        if fix_proc.stdout:
                            logger.error(f"Fixer STDOUT: {fix_proc.stdout}")

                # Proceed to TTS only if we have added translations and API key
                try:
                    if added:
                        languages = sorted(added.keys())
                        ids_set = set()
                        for _lang, _ids in added.items():
                            try:
                                ids_set.update(_ids)
                            except Exception:
                                pass
                        data_ids = sorted(ids_set)

                        if data_ids and languages:
                            if not os.getenv("OPENAI_API_KEY"):
                                logger.warning(
                                    "Skipping TTS regeneration at startup: OPENAI_API_KEY is not set"
                                )
                            else:
                                abs_output = os.path.abspath(OUTPUT_DIR)
                                cmd = [
                                    "python",
                                    os.path.join(
                                        "src",
                                        "regeneration",
                                        "scripts",
                                        "regenerate_tts.py",
                                    ),
                                    abs_output,
                                    "--language",
                                    ",".join(languages),
                                    "--data-ids",
                                    ",".join(data_ids),
                                ]
                                logger.info(
                                    "Executing startup TTS regeneration (background): "
                                    + f"langs={languages}, ids={len(data_ids)}"
                                )
                                try:
                                    result = subprocess.run(
                                        cmd,
                                        cwd=ADT_UTILS_DIR,
                                        capture_output=True,
                                        text=True,
                                        timeout=300,
                                    )
                                    if result.returncode == 0:
                                        logger.info(
                                            "Startup TTS regeneration completed successfully"
                                        )
                                    else:
                                        logger.error(
                                            f"Startup TTS regeneration failed (code {result.returncode})"
                                        )
                                        if result.stderr:
                                            logger.error(f"STDERR: {result.stderr}")
                                        if result.stdout:
                                            logger.error(f"STDOUT: {result.stdout}")
                                except Exception as sub_err:
                                    logger.error(
                                        f"Error running startup TTS subprocess: {sub_err}"
                                    )
                        else:
                            logger.info("No data-ids to regenerate TTS for at startup")
                    else:
                        logger.info(
                            "No added translations detected by fixer at startup"
                        )
                except Exception as tts_err:
                    logger.error(f"Startup TTS regeneration error: {tts_err}")

            asyncio.create_task(asyncio.to_thread(_run_startup_scripts_sync))
        except Exception as e:
            logger.error(f"Error scheduling startup scripts: {e}")

        yield

    app = FastAPI(
        title="ADT Chat Editor",
        description="API for the ADT Chat Editor service",
        version="0.0.1",
        docs_url="/docs",
        lifespan=lifespan,
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # In production, replace with specific origins
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add JWT authentication middleware
    app.add_middleware(JWTMiddleware)

    # Add pagination
    add_pagination(app)

    # Include the routers
    logger.info("Including routers")
    app.include_router(router)

    # Mount static files for frontend
    logger.info("Mounting frontend static files")
    app.mount(
        "/assets",
        NoCacheStaticFiles(directory="frontend/assets", html=True),
        name="assets",
    )

    # Mount input and output folders
    logger.info("Mounting input folder with directory")
    input_dir = os.path.join("data", "input")
    os.makedirs(input_dir, exist_ok=True)
    app.mount(
        "/input", NoCacheStaticFiles(directory=input_dir, html=True), name="input"
    )

    logger.info("Mounting output folders with directory")
    output_dir = os.path.join("data", "output")
    os.makedirs(output_dir, exist_ok=True)
    app.mount(
        "/output", NoCacheStaticFiles(directory=output_dir, html=True), name="output"
    )

    # Add SPA fallback route for client-side routing
    @app.get("/{full_path:path}")
    async def spa_fallback(request: Request, full_path: str):
        """Serve the frontend's index.html for SPA client-side routing."""
        # List of prefixes that should return 404 instead of SPA fallback
        api_prefixes = [
            "api/",
            "docs",
            "redoc",
            "openapi.json",
            "assets/",
            "input/",
            "output/",
            "vite.svg",
        ]

        # Check if the path starts with any API or static file prefix
        if any(full_path.startswith(prefix) for prefix in api_prefixes):
            raise HTTPException(status_code=404, detail="Not found")

        # Serve the React app for all other routes
        index_file = Path("frontend/index.html")
        if index_file.exists():
            return FileResponse(index_file)

        # Fallback if frontend index.html doesn't exist
        raise HTTPException(status_code=404, detail="Frontend not found")

    # Add a custom 404 handler
    @app.exception_handler(404)
    async def not_found(request: Request, exc: HTTPException):
        return HTMLResponse(content="Page not found", status_code=404)

    # Remove state checkpoints
    logger.info("Removing state checkpoints")
    if os.path.exists(STATE_CHECKPOINTS_DIR):
        shutil.rmtree(STATE_CHECKPOINTS_DIR)
        logger.info(f"State checkpoints directory removed at {STATE_CHECKPOINTS_DIR}")

    # Create state checkpoints dir
    os.makedirs(STATE_CHECKPOINTS_DIR, exist_ok=True)
    logger.info(f"State checkpoints directory created at {STATE_CHECKPOINTS_DIR}")

    return app


def main():
    """Run the FastAPI application."""
    uvicorn.run(
        "src.api.main:create_app",
        host="0.0.0.0",
        port=8000,
        log_level="info",
        reload=True,  # Enable auto-reload during development
    )


if __name__ == "__main__":
    main()
