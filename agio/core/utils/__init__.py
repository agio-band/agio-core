from pathlib import Path

from agio.core.core_config import CoreConfig
from agio.core.utils.app_context import AppContext
from agio.core.utils.app_dirs import get_agio_config_dir
from agio.core.utils.local_storage import LocalStorage

config = CoreConfig()
context = AppContext()
store = LocalStorage(Path(get_agio_config_dir()) / 'store')
