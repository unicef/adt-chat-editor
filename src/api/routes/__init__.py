"""Aggregate and expose API routers."""

from fastapi import APIRouter

from src.api.routes.adt_utils import router as adt_utils_router
from src.api.routes.chat import router as chat_router
from src.api.routes.frontend import router as frontend_router
from src.api.routes.health import router as health_router
from src.api.routes.publish import router as publish_router
from src.api.routes.setup import router as setup_router
from src.api.routes.terminal import router as terminal_router

# Create the main router
router = APIRouter()

# Include all routers
router.include_router(health_router)
router.include_router(chat_router)
router.include_router(frontend_router)
router.include_router(publish_router)
router.include_router(setup_router)
router.include_router(terminal_router)
router.include_router(adt_utils_router)
