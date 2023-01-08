import uuid
from typing import Generic, Optional, Type, TypeVar

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.db.db import Base


class Repository:
    def get_dir_info_by_path(self, *args, **kwargs):
        raise NotImplementedError

    def get_dir_info_by_id(self, *args, **kwargs):
        raise NotImplementedError

    def create_dir_info(self, *args, **kwargs):
        raise NotImplementedError


ModelType = TypeVar("ModelType", bound=Base)


class RepositoryDirectoryDB(Repository, Generic[ModelType]):
    def __init__(self, model: Type[ModelType]):
        self._model = model

    async def get_dir_info_by_path(self,
                                   db: AsyncSession,
                                   dir_path: str) -> Optional[ModelType]:
        if not dir_path.startswith('/'):
            dir_path = '/' + dir_path
        statement = select(self._model).where(self._model.path == dir_path)
        result = await db.execute(statement=statement)
        return result.scalar_one_or_none()

    async def get_dir_info_by_id(self,
                                 db: AsyncSession,
                                 dir_id: uuid.UUID) -> Optional[ModelType]:
        statement = select(self._model).where(self._model.id == dir_id)
        result = await db.execute(statement=statement)
        return result.scalar_one_or_none()
