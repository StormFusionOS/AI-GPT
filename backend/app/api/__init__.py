from fastapi import APIRouter

from .routes import ai, client, health, media, review, seo, system

api_router = APIRouter(prefix='/api')
api_router.include_router(client.router)
api_router.include_router(health.router)
api_router.include_router(media.router)
api_router.include_router(review.router)
api_router.include_router(seo.router)
api_router.include_router(ai.router)
api_router.include_router(system.router)

__all__ = ['api_router']
