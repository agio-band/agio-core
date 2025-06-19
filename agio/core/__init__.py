import os

from .core_config import CoreConfig

config = CoreConfig()


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


def get_agio_config_dir():
    agio_dir = os.path.join(_get_user_config_dir(), 'agio')
    os.makedirs(agio_dir, exist_ok=True)
    return agio_dir
