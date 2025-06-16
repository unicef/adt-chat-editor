from fastapi import APIRouter

from src.api.routes.books import router as books_router
from src.api.routes.chat import router as chat_router
from src.api.routes.health import router as health_router
from src.api.routes.publish import router as publish_router
from src.api.routes.frontend import router as frontend_router
from src.api.routes.setup import router as setup_router

# Create the main router
router = APIRouter()

# Include all routers
router.include_router(health_router)
router.include_router(books_router)
router.include_router(chat_router)
router.include_router(publish_router)
router.include_router(frontend_router)
router.include_router(setup_router)
