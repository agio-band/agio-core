from agio.tools import app_dirs, local_storage
from agio.tools import app_context

__all__ = ["store", "context"]

store = local_storage.LocalStorage(app_dirs.config_dir('local_store'))
context = app_context.AppContext()
