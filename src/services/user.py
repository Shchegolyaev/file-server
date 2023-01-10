from typing import Generic, Optional, Type, TypeVar, Union

from fastapi import Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from starlette import status

from src.core.config import app_settings
from src.db.db import Base, get_session
from src.models.models import User


class Repository:
    def get_by_username(self, *args, **kwargs):
        raise NotImplementedError

    def create(self, *args, **kwargs):
        raise NotImplementedError


ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)


class RepositoryUserDB(Repository, Generic[ModelType, CreateSchemaType]):
    oauth2_scheme = OAuth2PasswordBearer(tokenUrl='v1/token')

    def __init__(self, model: Type[ModelType]):
        self._model = model

    async def get_by_username(self,
                              db: AsyncSession,
                              obj_in: CreateSchemaType) -> Optional[ModelType]:
        obj_in_data = jsonable_encoder(obj_in)
        statement = select(self._model).where(
            self._model.username == obj_in_data['username'])
        results = await db.execute(statement=statement)
        return results.scalar_one_or_none()

    async def create(self,
                     db: AsyncSession,
                     obj_in: CreateSchemaType) -> ModelType:
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self._model(**obj_in_data)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get_token(self, db: AsyncSession, username: str, password: str):
        user: Union[User, None] = await self.authenticate(db,
                                                          username,
                                                          password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"})
        token = jwt.encode({'usr': user.username},
                           app_settings.secret_key,
                           algorithm='HS256')
        return token

    async def authenticate(self,
                           db: AsyncSession,
                           username: str,
                           password: str):
        user = await self.get_user_by_username(db=db, username=username)
        if not user:
            return False
        if user.password != password:
            return False
        return user

    async def _get_user_by_username(self, db: AsyncSession, username: str):
        statement = select(User).where(User.username == username)
        results = await db.execute(statement=statement)
        return results.scalar_one_or_none()

    async def get_current_user(self,
                               db: AsyncSession = Depends(get_session),
                               token: str = Depends(oauth2_scheme)):
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},)
        payload = jwt.decode(token,
                             app_settings.secret_key,
                             algorithms='HS256')
        username: str = payload.get("usr")
        if username is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail="Could not validate credentials",
                                headers={"WWW-Authenticate": "Bearer"},)
        user = await self._get_user_by_username(db=db, username=username)
        if user is None:
            raise credentials_exception
        return user
