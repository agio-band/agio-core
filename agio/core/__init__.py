from pathlib import Path

from .core_config import CoreConfig
from .utils.app_dirs import get_agio_config_dir
from .utils.local_storage import LocalStorage
from .utils.app_context import AppContext


__all__ = [
    'config',
    'store',
    'context'
]

# global constants

config = CoreConfig()
store = LocalStorage(Path(get_agio_config_dir()) / 'store')
context = AppContext()