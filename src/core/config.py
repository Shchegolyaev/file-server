import os
from logging import config as logging_config

from pydantic import BaseSettings, Field, PostgresDsn

from .logger import LOGGING

logging_config.dictConfig(LOGGING)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NUMBER_OF_DELETED_SYMBOLS = len(BASE_DIR.split('/')[-1]) + 1


class AppSettings(BaseSettings):
    app_title: str
    database_dsn: PostgresDsn
    project_name: str
    PROJECT_HOST: str
    PROJECT_PORT: int
    secret_key: str
    algorithm: str
    token_expire_minutes: int
    base_dir: str = Field(BASE_DIR, env='BASE_DIR')
    local_redis_url: str
    redis_url: str
    redis_host: str
    redis_port: int
    static_url: str
    files_folder_path: str = Field(
        os.path.join(
            BASE_DIR,
            'files'
        ),
        env='FILES_BASE_DIR'
    )
    compression_types: list = Field(
        ['zip', '7z', 'tar'],
        env='COMPRESSION_TYPES'
    )

    class Config:
        # env_file = '../../.env'
        env_file = os.path.dirname(BASE_DIR) + '/.env'


app_settings = AppSettings()
