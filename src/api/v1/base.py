import logging.config
from datetime import datetime
from typing import Any, Optional

import redis.asyncio as redis
from fastapi import (APIRouter, Depends, File, HTTPException, Query,
                     UploadFile, status)
from fastapi_cache.backends.redis import RedisCacheBackend
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import FileResponse, StreamingResponse

from src.core.config import app_settings
from src.db.db import get_session
from src.schemas import file_schemas
from src.schemas.user_schemas import CurrentUser
from src.services.base import file_crud, user_crud
from src.services.cache import (get_cache, get_cache_or_data, redis_cache,
                                set_cache)
from src.services.utils import (get_compressed_file_with_media_type,
                                get_file_info)

router = APIRouter()

logger = logging.getLogger(__name__)


@router.get('/files/list',
            response_model=file_schemas.FilesList,
            description='Get files list of current user.')
async def get_files(
        db: AsyncSession = Depends(get_session),
        current_user: CurrentUser = Depends(user_crud.get_current_user),
        cache: RedisCacheBackend = Depends(redis_cache)) -> Any:
    """
    Get list files on service.
    """
    redis_key = f'files_for_user_id_{str(current_user.id)}'
    data = await get_cache(cache, redis_key)
    if not data:
        files = await file_crud.get_list_by_user_object(db=db,
                                                        user_obj=current_user)
        file_list = [file_schemas.File.from_orm(file).dict() for file in files]
        data = {
            'account_id': current_user.id,
            'files': file_list
        }
        await set_cache(cache, data, redis_key)
    logger.info('Send list of files of %s', current_user.id)
    return data


@router.post('/files/upload',
             response_model=file_schemas.FileBase,
             status_code=status.HTTP_201_CREATED,
             description='Upload file to service.')
async def upload_file(
        path: str = Query(description='Path to directory or new file name '
                                      'start with /'),
        db: AsyncSession = Depends(get_session),
        current_user: CurrentUser = Depends(user_crud.get_current_user),
        file: UploadFile = File(...)):
    """
    Upload files to service.
    """
    if not path.startswith('/'):
        logger.info('Not correct path in request.')
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Path must starts with / .')
    #  check exist filename in path
    if path.split('/')[-1] == file.filename:
        full_path = path
    else:
        full_path = path + '/' + file.filename
    file_obj = await file_crud.create_or_put_file(db=db,
                                                  user_obj=current_user,
                                                  file_obj=file,
                                                  file_path=full_path)
    logger.info('Upload new file success.')
    return file_obj


@router.get('/files/download',
            status_code=status.HTTP_200_OK,
            description='Download file.')
async def download_file(
        db: AsyncSession = Depends(get_session),
        current_user: CurrentUser = Depends(user_crud.get_current_user),
        path: str = Query(description="[<path-to-file>||<file-meta-id>||"
                                      "<path-to-folder>||<folder-meta-id>] & "
                                      "compression_type=[zip||tar||7z]"),
        compression_type: Optional[str] = Query(default=None,
                                                description='(zip, 7z, tar) '
                                                            '(Optional).'),
        cache: RedisCacheBackend = Depends(redis_cache)) -> Any:
    """
    Download files/archive from service.
    """
    if not compression_type:
        file_by_path_redis_key = f'file_by_path_{path}'
        file_info = await get_cache_or_data(
            redis_key=file_by_path_redis_key,
            cache=cache,
            db_func_obj=get_file_info,
            data_schema=file_schemas.File,
            db_func_args=(db, path))
        if not file_info.get('is_downloadable'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Access dined.')
        return FileResponse(
            app_settings.files_folder_path + file_info.get('path'),
            media_type='application/octet-stream',
            filename=file_info.get('name'))
    if compression_type not in app_settings.compression_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'{compression_type} is not supported.')
    refreshed_io, media_type = await get_compressed_file_with_media_type(
        db=db,
        cache=cache,
        path=path,
        compression_type=compression_type)
    file_name = 'archive' + '.' + compression_type
    logger.info('User %s download file %s', current_user.id, path)
    return StreamingResponse(
        iter([refreshed_io.getvalue()]),
        media_type=media_type,
        headers={"Content-Disposition": f'attachment;filename={file_name}'})


@router.get('/ping',
            description="Ping postgres and redis",
            status_code=status.HTTP_200_OK)
async def ping(db: AsyncSession = Depends(get_session)):
    """
    Ping database and cache.
    """
    start_postgres = datetime.utcnow()
    status_postgres = await file_crud.check_db(db=db)
    if status_postgres != "Not available":
        status_postgres = (datetime.utcnow() - start_postgres).total_seconds()

    redis_connection = redis.Redis(host=app_settings.redis_host,
                                   port=app_settings.redis_port,
                                   decode_responses=True)
    start_redis = datetime.utcnow()
    try:
        await redis_connection.ping()
        status_redis = (datetime.utcnow() - start_redis).total_seconds()
    except Exception:
        status_redis = "Not available"
    logger.info('Send ping.')
    return {"db": status_postgres, "cache": status_redis}
