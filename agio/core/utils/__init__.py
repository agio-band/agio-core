from pathlib import Path

from agio.core.core_config import CoreConfig
from agio.core.utils.context import AppContext
from agio.core.utils.app_dirs import config_dir, pipeline_config_dir
from agio.core.utils.local_storage import LocalStorage
from .actions import get_actions

__all__ = [
    'config',
    'context',
    'store',
    'get_actions',
    'config_dir',
    'pipeline_config_dir',
]

config = CoreConfig()
context = AppContext()
store = LocalStorage(Path(pipeline_config_dir()) / 'store')
