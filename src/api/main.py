import os
import shutil

import uvicorn
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi_pagination import add_pagination
from starlette.responses import FileResponse
from starlette.staticfiles import StaticFiles

from src.api.routes import router
from src.settings import custom_logger, STATE_CHECKPOINTS_DIR

# Create the logger
logger = custom_logger(__name__)


# NoCache STATICFIELD
class NoCacheStaticFiles(StaticFiles):
    async def get_response(self, path, scope):
        response: FileResponse = await super().get_response(path, scope)
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response


# Create the app
def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    logger.info("Creating FastAPI app")
    app = FastAPI(
        title="ADT Chat Editor",
        description="API for the ADT Chat Editor service",
        version="0.0.1",
        docs_url="/docs",
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # In production, replace with specific origins
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add pagination
    add_pagination(app)

    # Include the routers
    logger.info("Including routers")
    app.include_router(router)

    # Mount static files for frontend
    logger.info("Mounting frontend static files")
    app.mount(
        "/assets", NoCacheStaticFiles(directory="frontend/assets", html=True), name="assets"
    )

    # Mount input and output folders
    logger.info("Mounting input and output folders with directory")
    app.mount(
        "/output", NoCacheStaticFiles(directory="data/output", html=True), name="output"
    )

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
