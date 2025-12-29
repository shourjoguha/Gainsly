"""API routes module."""
from app.api.routes.programs import router as programs_router
from app.api.routes.days import router as days_router
from app.api.routes.logs import router as logs_router
from app.api.routes.settings import router as settings_router

__all__ = [
    "programs_router",
    "days_router",
    "logs_router",
    "settings_router",
]
