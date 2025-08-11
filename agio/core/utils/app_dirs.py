import os
import tempfile
from pathlib import Path


def _get_user_config_dir():
    if os.name == 'nt':
        return os.getenv('APPDATA')
    elif os.name == 'posix':
        if 'XDG_CONFIG_HOME' in os.environ:
            return os.environ['XDG_CONFIG_HOME']
        else:
            return os.path.join(os.path.expanduser('~'), '.config')
    elif os.name == 'mac':
        return os.path.join(os.path.expanduser('~'), 'Library', 'Application Support')
    else:
        raise OSError("Unsupported operating system")


def _get_user_cache_dir():
    if os.name == 'nt':
        path = Path(os.getenv("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    elif os.name == "darwin":
        path = Path.home() / "Library" / "Caches"
    else:
        path = Path(os.getenv("XDG_CACHE_HOME", Path.home() / ".cache"))
    return path.expanduser()


def _get_user_temp_dir():
    return Path(tempfile.gettempdir())


def temp_dir() -> Path:
    return _get_user_temp_dir().joinpath('agio')


def cache_dir() -> Path:
    return _get_user_cache_dir().joinpath('agio')


def local_app_dir() -> Path:
    return Path(_get_user_config_dir(), 'agio')


def config_dir() -> Path:
    return local_app_dir() / 'config'


def settings_dir() -> Path:
    return local_app_dir() / 'settings'


def default_workspace_install_dir() -> Path:
    return local_app_dir() / 'workspaces'


def pipeline_config_dir() -> Path:
    return local_app_dir() / 'pipe'
