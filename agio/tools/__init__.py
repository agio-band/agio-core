from agio.tools import app_dirs, local_storage
from .context_app import app

__all__ = ["store",  "app"]

store = local_storage.LocalStorage(app_dirs.config_dir('local_store'))
