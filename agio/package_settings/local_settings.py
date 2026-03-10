from pydantic import BaseModel

from agio.core.settings import APackageSettings
from agio.tools import local_dirs


class ApplicationSettings(BaseModel):
    name: str
    version: str
    install_dir: str



class CoreSettings(APackageSettings):
    applications: list[ApplicationSettings] = ()
    workspaces_root: str = lambda: local_dirs.default_env_install_dir().as_posix()  # TODO add supporting annotation str|Path

