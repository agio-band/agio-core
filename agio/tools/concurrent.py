import asyncio
import contextvars
import threading
from typing import Callable, Any


class AsyncContextProxy:
    def __init__(self, object_class: Callable, *args, **kwargs):
        self._object_class = object_class
        self._default_args = args
        self._default_kwargs = kwargs

        self._obj_var = contextvars.ContextVar("proxy_obj", default=None)
        self._cfg_var = contextvars.ContextVar("proxy_cfg", default=None)

    def configure_local_object(self, *args, **kwargs):
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            raise RuntimeError("AsyncContextProxy.configure_local_object() must be called within a running event loop.")

        self._cfg_var.set((args, kwargs))
        self._obj_var.set(None)

    def _get_object(self) -> Any:
        obj = self._obj_var.get()
        if obj is None:
            cfg = self._cfg_var.get()
            args, kwargs = cfg if cfg else (self._default_args, self._default_kwargs)
            obj = self._object_class(*args, **kwargs)
            self._obj_var.set(obj)
        return obj

    def __getattr__(self, name):
        return getattr(self._get_object(), name)


class ThreadContextProxy:
    def __init__(self, object_class: Callable, *args, **kwargs):
        self._object_class = object_class
        self._default_args = args
        self._default_kwargs = kwargs
        self._local = threading.local()

    def configure_local_object(self, *args, **kwargs):
        self._local.args = args
        self._local.kwargs = kwargs
        if hasattr(self._local, "object"):
            del self._local.object

    def _get_object(self) -> Any:
        if not hasattr(self._local, "object"):
            args = getattr(self._local, "args", self._default_args)
            kwargs = getattr(self._local, "kwargs", self._default_kwargs)
            self._local.object = self._object_class(*args, **kwargs)
        return self._local.object

    def __getattr__(self, name):
        return getattr(self._get_object(), name)

