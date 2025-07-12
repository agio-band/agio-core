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
        path = os.getenv("LOCALAPPDATA", Path.home() / "AppData" / "Local")
    elif os.name == "darwin":
        path = Path.home() / "Library" / "Caches"
    else:
        path = Path(os.getenv("XDG_CACHE_HOME", Path.home() / ".cache"))
    return path.expanduser()


def _get_user_temp_dir():
    return Path(tempfile.gettempdir())


def temp_dir() -> str:
    return _get_user_temp_dir().joinpath('agio').as_posix()


def cache_dir() -> str:
    return _get_user_cache_dir().joinpath('agio').as_posix()


def config_dir() -> str:
    conf_dir = Path(_get_user_config_dir(), 'agio')
    return conf_dir.as_posix()


def pipeline_config_dir() -> str:
    path = os.path.join(config_dir(), 'pipe')
    return path
