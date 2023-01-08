import logging
import os
import tarfile
import zipfile
from io import BytesIO

import py7zr
from fastapi import HTTPException
from fastapi_cache.backends.redis import RedisCacheBackend
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from src.core.config import app_settings
from src.schemas import file_schemas
from src.services.base import directory_crud, file_crud
from src.services.cache import get_cache_or_data

logger = logging.getLogger(__name__)


async def get_file_info(db: AsyncSession, path: str):
    if path.find('/') != -1:
        file_info = await file_crud.get_file_info_by_path(db=db,
                                                          file_path=path)
    else:
        file_info = await file_crud.get_file_info_by_id(db=db, file_id=path)
    if not file_info:
        logger.error('Raise 404 for file with path/id %s', path)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='File not found'
        )
    return file_info


async def get_path_by_id(db: AsyncSession,
                         obj_id: str,
                         cache: RedisCacheBackend) -> str:
    redis_key = f'get_path_by_id_{obj_id}'
    file_info = await get_cache_or_data(
        redis_key=redis_key,
        cache=cache,
        db_func_obj=file_crud.get_file_info_by_id,
        data_schema=file_schemas.PathSchema,
        db_func_args=(db, obj_id),
        cache_expire=3600)
    if not file_info:
        dir_info = await get_cache_or_data(
            redis_key=redis_key,
            cache=cache,
            db_func_obj=directory_crud.get_dir_info_by_id,
            data_schema=file_schemas.PathSchema,
            db_func_args=(db, obj_id),
            cache_expire=3600)
        if not dir_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Directory or file not found')
        return dir_info.get()
    return file_info.get('path')


def get_files_paths_by_folder(full_path: str) -> list:
    return [
        os.path.join(full_path, f)
        for f in os.listdir(full_path)
        if os.path.isfile(os.path.join(full_path, f))]


def compress_file(
        write_to_file_func, full_path: str) -> None:
    if os.path.isfile(full_path):
        write_to_file_func(full_path)
    else:
        files_paths = get_files_paths_by_folder(full_path)
        for file_path in files_paths:
            write_to_file_func(file_path)


def compress(io_obj: BytesIO,
             path: str,
             compression_type: str):
    full_path = app_settings.files_folder_path + path
    if compression_type == 'zip':
        with zipfile.ZipFile(io_obj, mode='w',
                             compression=zipfile.ZIP_DEFLATED) as zip_io:
            compress_file(
                write_to_file_func=zip_io.write,
                full_path=full_path
            )
            zip_io.close()
        return io_obj, 'application/x-zip-compressed'
    elif compression_type == 'tar':
        with tarfile.open(fileobj=io_obj, mode='w:gz') as tar:
            compress_file(
                write_to_file_func=tar.add,
                full_path=full_path
            )
            tar.close()
        return io_obj, 'application/x-gtar'
    elif compression_type == '7z':
        with py7zr.SevenZipFile(io_obj, mode='w') as seven_zip:
            compress_file(
                write_to_file_func=seven_zip.write,
                full_path=full_path
            )
        return io_obj, 'application/x-7z-compressed'
    else:
        return 'Error format archive'


async def get_compressed_file_with_media_type(db: AsyncSession,
                                              cache: RedisCacheBackend,
                                              path: str,
                                              compression_type: str
                                              ) -> tuple[BytesIO, str]:
    io_obj = BytesIO()
    if path.find('/') == -1:
        path = await get_path_by_id(db=db,
                                    obj_id=path,
                                    cache=cache)
    if not path.startswith('/'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Path must starts with / .'
        )
    refreshed_io, media_type = compress(
        io_obj=io_obj,
        path=path,
        compression_type=compression_type)
    return refreshed_io, media_type
