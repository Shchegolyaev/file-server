from src.models.models import Directory, File, User
from src.schemas.user_schemas import UserRegister

from .directory import RepositoryDirectoryDB
from .files import RepositoryFileDB
from .user import RepositoryUserDB


class RepositoryUser(RepositoryUserDB[User, UserRegister]):
    pass


class RepositoryFile(RepositoryFileDB[File]):
    pass


class RepositoryDirectory(RepositoryDirectoryDB[File]):
    pass


user_crud = RepositoryUser(User)
file_crud = RepositoryFile(File)
directory_crud = RepositoryDirectory(Directory)
