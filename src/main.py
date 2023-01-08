import uvicorn
from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
from fastapi_cache import caches, close_caches
from fastapi_cache.backends.redis import CACHE_KEY, RedisCacheBackend

from src.api.v1.auth import router as auth_router
from src.api.v1.base import router as base_router
from src.core.config import app_settings

app = FastAPI(
    title=app_settings.app_title,
    docs_url='/api/openapi',
    openapi_url='/api/openapi.json',
    default_response_class=ORJSONResponse,
    swagger_ui_oauth2_redirect_url='/token')

app.include_router(base_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")


@app.on_event('startup')
async def on_startup() -> None:
    rc = RedisCacheBackend(app_settings.redis_url)
    caches.set(CACHE_KEY, rc)


@app.on_event('shutdown')
async def on_shutdown() -> None:
    await close_caches()

if __name__ == '__main__':
    uvicorn.run(
        'main:app',
        host=app_settings.PROJECT_HOST,
        port=app_settings.PROJECT_PORT,
    )
