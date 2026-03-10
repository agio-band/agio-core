import shutil

from diskcache import Cache, Lock

from agio.tools import local_dirs

__cache_locker = Cache(local_dirs.temp_dir('locker').as_posix())


def locker(name, expire=60):
    if expire <= 0:
        raise RuntimeError('The lock will not work if the expiration time is zero or less.')
    return Lock(__cache_locker, name, expire=expire)


def reset_locker(existing_locker):
    shutil.rmtree(existing_locker._cache.directory)