from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, validator


class User(BaseModel):
    username: str


class UserRegister(User):
    password: str


class UserRegisterResp(BaseModel):
    status: str


class UserAuth(User):
    password: str


class UserAuthResp(User):
    status: str


class Token(BaseModel):
    token: str


class CurrentUser(User):
    id: UUID
    created_at: datetime

    @validator('created_at', pre=True)
    def datetime_to_str(cls, value):
        if isinstance(value, str):
            return datetime.fromisoformat(value)
