from diskcache import Cache, Lock

from agio.tools import app_dirs

__cache_locker = Cache(app_dirs.temp_dir('locker').as_posix())


def locker(name, expire=60):
    if expire == 0:
        raise RuntimeError('Locker does not work if the expiration time is zero.')
    return Lock(__cache_locker, name, expire=expire)
