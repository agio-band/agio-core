import shutil
import threading
from typing import Callable

from diskcache import Cache, Lock

from agio.tools import local_dirs

__cache_locker = Cache(local_dirs.temp_dir('locker').as_posix())


def locker(name, expire=60):
    if expire <= 0:
        raise RuntimeError('The lock will not work if the expiration time is zero or less.')
    return Lock(__cache_locker, name, expire=expire)


def reset_locker(existing_locker):
    shutil.rmtree(existing_locker._cache.directory)


class ThreadLocalProxy:
    def __init__(self, object_class: Callable, configure_required: bool = False):
        self._local = threading.local()
        self._object_class = object_class
        self.configure_required = configure_required
        self.configured = False

    def configure_thread(self, *args, **kwargs):
        self._local.args = args
        self._local.kwargs = kwargs
        self.configured = True

    def _get_object(self) -> object:
        if self.configure_required and not self.configured:
            raise RuntimeError(f'Threaded object {self._object_class.__name__} is not configured.')
        if not hasattr(self._local, "object"):
            args = getattr(self._local, "args", ())
            kwargs = getattr(self._local, "kwargs", {})
            self._local.object = self._object_class(*args, **kwargs)
        return self._local.object

    def __getattr__(self, name):
        return getattr(self._get_object(), name)


