from pydantic import BaseModel

from agio.core.settings import APackageSettings
from agio.tools import app_dirs


class Application(BaseModel):
    name: str
    version: str
    install_dir: str



class CoreSettings(APackageSettings):
    applications: list[Application] = ()
    workspaces_root: str = lambda: app_dirs.default_env_install_dir().as_posix()  # TODO add supporting annotation str|Path

