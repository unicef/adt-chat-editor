import os
import shutil

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_pagination import add_pagination

from src.api.routes import router
from src.settings import custom_logger, STATE_CHECKPOINTS_DIR


# Create the logger
logger = custom_logger(__name__)


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
