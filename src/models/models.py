import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy_utils import UUIDType

from src.db.db import Base


class User(Base):
    __tablename__ = 'users'
    id = Column(UUIDType(binary=False), primary_key=True, default=uuid.uuid1)
    username = Column(String(125), nullable=False, unique=True)
    password = Column(String(125), nullable=False)
    files = relationship('File', back_populates="user", passive_deletes=True)
    created_at = Column(DateTime, index=True, default=datetime.utcnow)


class File(Base):
    __tablename__ = 'files'
    id = Column(UUIDType(binary=False), primary_key=True, default=uuid.uuid1)
    user_id = Column(UUIDType, ForeignKey('users.id', ondelete="CASCADE"),
                     nullable=False, index=True)
    user = relationship("User", back_populates="files")
    name = Column(String(125), nullable=False)
    created_at = Column(DateTime, index=True, default=datetime.utcnow)
    path = Column(String(255), nullable=False, unique=True)
    size = Column(Integer, nullable=False)
    is_downloadable = Column(Boolean, default=False)


class Directory(Base):
    __tablename__ = 'directories'
    id = Column(UUIDType(binary=False), primary_key=True, default=uuid.uuid1)
    path = Column(String(255), nullable=False, unique=True)
