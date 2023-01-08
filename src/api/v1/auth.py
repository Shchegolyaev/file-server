import logging.config
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.db import get_session
from src.schemas import user_schemas
from src.services.base import user_crud

router = APIRouter()

logger = logging.getLogger(__name__)


@router.post('/register',
             response_model=user_schemas.UserRegisterResp,
             status_code=status.HTTP_201_CREATED,
             description='Registration.')
async def create_user(input_user: user_schemas.UserRegister,
                      db: AsyncSession = Depends(get_session)) -> Any:
    """
    Registration.
    """
    user_obj = await user_crud.get_by_username(db=db, obj_in=input_user)
    if user_obj:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail='Already exist.')
    user_obj = await user_crud.create(db=db, obj_in=input_user)
    logger.info(f'User {user_obj.username} register successful')
    return user_schemas.UserRegisterResp(status="Success registered.")


@router.post("/auth",
             response_model=user_schemas.Token,
             description="Return token.")
async def get_token_for_user(input_user: user_schemas.UserAuth,
                             db: AsyncSession = Depends(get_session)):
    """
    Generate token.
    """
    token = await user_crud.get_token(db=db,
                                      username=input_user.username,
                                      password=input_user.password)
    logger.info("Generate token success.")
    return user_schemas.Token(token=token)


@router.post('/token', description="Endpoint for auth in docs")
async def login_ui_for_access_token(
        db: AsyncSession = Depends(get_session),
        form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Auth for test in docs FastApi.
    """
    token = await user_crud.get_token(db=db,
                                      username=form_data.username,
                                      password=form_data.password)
    logger.info(f"Return token {form_data.username} in docs.")
    return {'access_token': token, 'token_type': 'bearer'}
