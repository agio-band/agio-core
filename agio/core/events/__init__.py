import logging
from contextlib import contextmanager
from pathlib import Path
from typing import Callable, Any

from agio.core.events.event_hub import EventHub
from agio.tools.modules import import_module_by_path
from .event import AEvent

logger = logging.getLogger(__name__)
event_hub = EventHub()


def emit(event_name: str, payload: Any = None) -> None:
    if payload is not None:
        if not isinstance(payload, dict):
            raise TypeError("payload must be a dict")
    return event_hub.emit(event_name, payload)


def subscribe(event_name: str|list[str], callback_func: Callable = None, /, raise_error=False, **kwargs):
    if not callback_func:
        # used as decorator
        def wrapper(func):
            added = event_hub.add_callback(event_name, func, raise_error=raise_error, **kwargs)
            logger.debug(f"Subscribe event '{event_name}' to {func.__name__}: {len(added)}")
            return bool(added)
        return wrapper
    else:
        added = event_hub.add_callback(event_name, callback_func, raise_error=raise_error, **kwargs)
        logger.debug(f"Subscribe event '{event_name}' to {callback_func.__name__}: {len(added)}")
        return bool(added)

def unsubscribe(callback_func: Callable, event_name: str = None):
    removed = event_hub.remove_callback(callback_func, event_name)
    event_name = event_name or 'ALL'
    logger.debug(f"Unsubscribe event {callback_func.__name__} from event '{event_name}': {removed}")
    return removed


def on_startup(callback_func: Callable):
    """
    Shortcut for startup event
    """
    return subscribe('core.app.startup', callback_func)


def on_exit(callback_func: Callable):
    """Shortcut for exit event"""
    return subscribe('core.app.exit', callback_func)



def callback(event_name: str, **kwargs):
    def decorator(func: Callable):
        subscribe(event_name, func, **kwargs)
        return func
    return decorator


@contextmanager
def subscribe_manager(event_name, func, raise_error=False, **kwargs):
    """
    Temporary subscribe
    """
    try:
        yield subscribe(event_name, func, raise_error=raise_error, **kwargs)
    finally:
        unsubscribe(func, event_name)


def register_callbacks(path_list: list[str]):
    for path, pkg in path_list:
        rel_path = Path(path).relative_to(pkg.root.parent)
        name = '.'.join([*rel_path.parts[:-1], Path(path).stem])
        import_module_by_path(path, name)
