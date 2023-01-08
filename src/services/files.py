import os
from datetime import datetime
from typing import Generic, Optional, Type, TypeVar

from aioshutil import copyfileobj
from fastapi import File as FileObj
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.core.config import app_settings
from src.db.db import Base
from src.models.models import File, User


class Repository:
    def get_file_info_by_path(self, *args, **kwargs):
        raise NotImplementedError

    def get_file_info_by_id(self, *args, **kwargs):
        raise NotImplementedError

    def get_list_by_user_object(self, *args, **kwargs):
        raise NotImplementedError

    def create_or_put_file(self, *args, **kwargs):
        raise NotImplementedError


ModelType = TypeVar("ModelType", bound=Base)


class RepositoryFileDB(Repository, Generic[ModelType]):
    def __init__(self, model: Type[ModelType]):
        self._model = model

    async def write_to_file(self,
                            file_obj: FileObj,
                            full_file_path: str, ):
        with open(full_file_path, 'wb') as buffer:
            await copyfileobj(file_obj.file, buffer)

    async def create_file(self,
                          db: AsyncSession,
                          file_path: str,
                          full_file_path: str,
                          create_dir_info,
                          file_obj: FileObj,
                          model: Type[File],
                          user_obj: Type[User]):
        path = app_settings.files_folder_path
        for dir_name in file_path.split('/')[1:-1]:
            path = os.path.join(path, dir_name)
            if os.path.exists(path):
                continue
            else:
                os.mkdir(path)
                await create_dir_info(db=db, path=path)
        await self.write_to_file(file_obj=file_obj,
                                 full_file_path=full_file_path)
        size = os.path.getsize(full_file_path)
        new_file = model(name=file_obj.filename,
                         path=file_path,
                         size=size,
                         is_downloadable=True,
                         user=user_obj)
        db.add(new_file)
        await db.commit()
        await db.refresh(new_file)
        return new_file

    async def put_file(self,
                       db: AsyncSession,
                       file_obj: FileObj,
                       full_file_path: str,
                       file_info: Type[File]):
        await self.write_to_file(
            file_obj=file_obj,
            full_file_path=full_file_path
        )
        size = os.path.getsize(full_file_path)
        file_info.size = size
        file_info.created_at = datetime.utcnow()
        await db.commit()
        await db.refresh(file_info)
        return file_info

    async def get_file_info_by_path(self,
                                    db: AsyncSession,
                                    file_path: str) -> Optional[ModelType]:
        if not file_path.startswith('/'):
            file_path = '/' + file_path
        statement = select(self._model).where(self._model.path == file_path)
        result = await db.execute(statement=statement)
        return result.scalar_one_or_none()

    async def check_db(self, db: AsyncSession):
        status = "Available"
        try:
            statement = select(File)
            await db.execute(statement=statement)
        except Exception:
            status = "Not available"
        return status

    async def get_file_info_by_id(self,
                                  db: AsyncSession,
                                  file_id: str) -> Optional[ModelType]:
        statement = select(self._model).where(self._model.id == file_id)
        result = await db.execute(statement=statement)
        return result.scalar_one_or_none()

    async def get_list_by_user_object(self,
                                      db: AsyncSession,
                                      user_obj: ModelType,
                                      ) -> list[ModelType]:
        statement = select(self._model).where(
            self._model.user_id == user_obj.id)
        results = await db.execute(statement=statement)
        return results.scalars().all()

    async def create_dir_info(self,
                              db: AsyncSession,
                              path: str) -> ModelType:
        dir_info_obj = self._model(path=path)
        db.add(dir_info_obj)
        await db.commit()
        await db.refresh(dir_info_obj)
        return dir_info_obj

    async def create_or_put_file(self,
                                 db: AsyncSession,
                                 user_obj: ModelType,
                                 file_obj: FileObj,
                                 file_path: str) -> Optional[ModelType]:
        file_in_storage = await self.get_file_info_by_path(db=db,
                                                           file_path=file_path)
        full_file_path = app_settings.files_folder_path + file_path
        if file_in_storage:
            return await self.put_file(
                db=db,
                full_file_path=full_file_path,
                file_info=file_in_storage,
                file_obj=file_obj)
        else:
            return await self.create_file(
                db=db,
                file_path=file_path,
                full_file_path=full_file_path,
                create_dir_info=self.create_dir_info,
                file_obj=file_obj,
                model=self._model,
                user_obj=user_obj)
