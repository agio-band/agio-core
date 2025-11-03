from agio.core.settings import APackageSettings
from agio.tools import app_dirs


class CoreSettings(APackageSettings):
    workspaces_root: str = lambda: app_dirs.default_env_install_dir().as_posix()  # TODO add supporting annotation str|Path

