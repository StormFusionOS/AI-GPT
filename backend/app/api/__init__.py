from fastapi import APIRouter

from .routes import health, media

api_router = APIRouter(prefix='/api')
api_router.include_router(health.router)
api_router.include_router(media.router)

__all__ = ['api_router']
