from agio.tools import local_dirs, local_storage

__all__ = ["store"]

store = local_storage.LocalStorage(local_dirs.config_dir('local_store'))
