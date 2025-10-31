from fastapi import APIRouter

from .routes import client, health, media, system

api_router = APIRouter(prefix='/api')
api_router.include_router(client.router)
api_router.include_router(health.router)
api_router.include_router(media.router)
api_router.include_router(system.router)

__all__ = ['api_router']
