import contextlib
import contextvars
import logging
from typing import Callable, Any


logger = logging.getLogger(__name__)


class ContextVarProxy:
    """
    Separate client for different threads or coroutines
    """
    def __init__(self, object_class: Callable, *args, **kwargs):
        self._object_class = object_class
        self._cv_config: contextvars.ContextVar[tuple[tuple, dict]] = contextvars.ContextVar(
            f"proxy_config_{id(self)}", default=(args, kwargs)
        )
        self._cv_object: contextvars.ContextVar[object | None] = contextvars.ContextVar(
            f"proxy_obj_{id(self)}", default=None
        )

    @contextlib.contextmanager
    def configure_context(self, *args, **kwargs):
        """for для with"""
        tok_cfg = self._cv_config.set((args, kwargs))
        tok_obj = self._cv_object.set(None)
        try:
            yield self
        finally:
            self._cv_object.reset(tok_obj)
            self._cv_config.reset(tok_cfg)

    @contextlib.asynccontextmanager
    async def aconfigure_context(self, *args, **kwargs):
        """for async with"""
        tok_cfg = self._cv_config.set((args, kwargs))
        tok_obj = self._cv_object.set(None)
        try:
            yield self
        finally:
            self._cv_object.reset(tok_obj)
            self._cv_config.reset(tok_cfg)

    def _get_object(self) -> Any:
        obj = self._cv_object.get()
        if obj is None:
            args, kwargs = self._cv_config.get()
            obj = self._object_class(*args, **kwargs)
            self._cv_object.set(obj)
        return obj

    def __getattr__(self, name: str) -> Any:
        return getattr(self._get_object(), name)


