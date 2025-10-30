from fastapi import APIRouter

router = APIRouter(tags=['health'])


@router.get('/health', summary='Application health check')
async def health_check() -> dict[str, str]:
    return {'status': 'ok'}
