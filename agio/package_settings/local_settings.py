from pydantic import BaseModel, Field

from agio.core.settings import APackageSettings
from agio.tools import local_dirs


class ApplicationSettings(BaseModel):
    name: str
    version: str
    install_dir: str
    workdir: str = None
    extra_args: str = None
    extra_envs: dict[str, str] = Field(default_factory=dict)
    custom_data: dict = None
    python_version: str = None



class CoreSettings(APackageSettings):
    applications: list[ApplicationSettings] = ()
    workspaces_root: str = lambda: local_dirs.default_env_install_dir().as_posix()  # TODO add supporting annotation str|Path

