import json
import uuid
from datetime import datetime
from typing import Callable, Type

from fastapi_cache import caches
from fastapi_cache.backends.redis import CACHE_KEY, RedisCacheBackend
from pydantic import BaseModel


def redis_cache():
    return caches.get(CACHE_KEY)


def serialized_data(value):
    if isinstance(value, datetime):
        return value.isoformat()
    elif isinstance(value, uuid.UUID):
        return str(value)
    return value


async def set_cache(
        cache: RedisCacheBackend,
        data: dict,
        redis_key: str,
        expire: int = 30
):
    await cache.set(
        key=redis_key,
        value=json.dumps(data, default=serialized_data),
        expire=expire
    )


async def get_cache(cache: RedisCacheBackend, redis_key: str) -> dict:
    data = await cache.get(redis_key)
    if data:
        data = json.loads(data)
    return data


async def get_cache_or_data(redis_key: str,
                            cache: RedisCacheBackend,
                            db_func_obj: Callable,
                            data_schema: Type[BaseModel],
                            db_func_args: tuple = (),
                            db_func_kwargs: dict = {},
                            cache_expire: int = 30):
    data = await get_cache(cache, redis_key)
    if not data:
        data = await db_func_obj(*db_func_args, **db_func_kwargs)
        if data:
            data = data_schema.from_orm(data).dict()
            await set_cache(cache=cache,
                            data=data,
                            redis_key=redis_key,
                            expire=cache_expire)
        else:
            return None
    return data
