import logging
from contextlib import contextmanager
from typing import Callable, Any

from .event_hub import EventHub
from ..utils.import_utils import import_module_by_path

logger = logging.getLogger()
event_hub = EventHub()


def emit(event_name: str, payload: Any = None) -> None:
    return event_hub.emit(event_name, payload)


def subscribe(event_name: str, callback_func: Callable, raise_error=False, **kwargs):
    added = event_hub.add_callback(event_name, callback_func, raise_error=raise_error, **kwargs)
    logger.debug(f"Subscribe event '{event_name}' to {callback_func.__name__}: {added}")
    return added


def unsubscribe(callback_func: Callable, event_name: str = None):
    removed = event_hub.remove_callback(callback_func, event_name)
    logger.debug(f"Unsubscribe event {callback_func.__name__} from event '{event_name or "ALL"}': {removed}")
    return removed


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
    for p in path_list:
        import_module_by_path(p)

    # import sys
    # import types
    #
    # callbacks_module = types.ModuleType('callbacks_module')
    # sys.modules['callbacks_module'] = callbacks_module
    # clb_list = {}
    # setattr(callbacks_module, 'callbacks', clb_list)
    # for p in path_list:
    #     mod = import_module_by_path(p)
    #     clb_list[p] = mod
