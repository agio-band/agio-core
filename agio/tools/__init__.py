from functools import cache


__all__ = ["get_store"]


@cache
def get_store():
    from agio.tools import local_dirs, local_storage

    return local_storage.LocalStorage(local_dirs.config_dir('local_store'))
