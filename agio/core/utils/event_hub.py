import logging
from collections import defaultdict
from fnmatch import fnmatch
from typing import Callable

from agio.core.events.event import AEvent
from agio.core.exceptions import StopEventPropagate, EventRuntimeError, CallbackInitError
from agio.core.utils.singleton import Singleton

logger = logging.getLogger(__name__)


class EventHub(metaclass=Singleton):
    """Registering callbacks and executing them when an event occurs"""
    def __init__(self):
        self._callbacks: defaultdict[str, dict[Callable, dict]] = defaultdict(dict)

    def __check_event_name(self, event_name: str):
        if not isinstance(event_name, str):
            raise CallbackInitError("Event name must be a string")
        if not event_name.strip():
            raise CallbackInitError("Event name must not be empty")

    def __check_callback(self, callback: Callable):
        if not callable(callback):
            raise CallbackInitError("Callback must be callable")

    def add_callback(self, event_name: str|str, callback: Callable, **kwargs) -> list[str]:
        if isinstance(event_name, str):
            event_name = [event_name]
        added = []
        for name in event_name:
            self.__check_event_name(name)
            self.__check_callback(callback)

            if callback in self._callbacks[name]:
                logger.debug(f"Callback {getattr(callback, '__name__', str(callback))} for event {name} already exists.")
            else:
                self._callbacks[name][callback] = {
                    "once": kwargs.get("once", False),
                    "raise_error": kwargs.get("raise_error", False),
                    "name": getattr(callback, '__name__', str(callback))
                }
                logger.debug(f"Adding callback {self._callbacks[name][callback]['name']} for event {name}")
                added.append(name)
        return added

    def remove_callback(self, callback: Callable, event_name: str = None) -> bool:
        self.__check_callback(callback)

        removed_count = 0
        if event_name is None:
            for event_cbs in list(self._callbacks.values()):
                if callback in event_cbs:
                    event_cbs.pop(callback)
                    removed_count += 1
            self._callbacks = defaultdict(dict, {
                event: cbs for event, cbs in self._callbacks.items() if cbs
            })
        else:
            if event_name in self._callbacks and callback in self._callbacks[event_name]:
                self._callbacks[event_name].pop(callback)
                removed_count = 1
                if not self._callbacks[event_name]:
                    self._callbacks.pop(event_name)
        return bool(removed_count)

    def emit(self, event_name: str, payload: dict):
        callbacks_to_remove = []

        sender = None
        event_obj = AEvent(event_name, sender)
        for event_pattern, callbacks_dict in list(self._callbacks.items()):
            if not fnmatch(event_name, event_pattern):
                continue

            for callback_func, metadata in list(callbacks_dict.items()):
                try:
                    ##### EXECUTE CALLBACK #####
                    callback_func(event_obj, payload)
                    ############################
                except StopEventPropagate:
                    logger.debug(f"Event propagation stopped by {metadata['name']} for event {event_name}")
                    break
                except EventRuntimeError:
                    logger.error(f"Event runtime error in {metadata['name']} for event {event_name}")
                    raise
                except Exception as e:
                    if metadata["raise_error"]:
                        logger.exception(f"Callback {metadata['name']} for event {event_name} raised an error (re-raising).")
                        raise
                    else:
                        logger.exception(f"Callback {metadata['name']} for event {event_name} failed (error suppressed).")
                finally:
                    if metadata["once"]:
                        callbacks_to_remove.append((callback_func, event_pattern))

        for callback_func, event_pattern in callbacks_to_remove:
            self.remove_callback(callback_func, event_pattern)

    def clear(self):
        self._callbacks.clear()

    def callback_registered(self, callback: Callable) -> bool:
        self.__check_callback(callback)
        for callbacks in self._callbacks.values():
            if callback in callbacks:
                return True
        return False

    def print_event_list(self):
        if not self._callbacks:
            print("No events registered.")
            return

        for event_name in self._callbacks:
            print(f"[{event_name}]")
            if not self._callbacks[event_name]:
                print("  (No callbacks)")
                continue
            for callback_func, metadata in self._callbacks[event_name].items():
                print(f"  {metadata['name']}(){' [once]' if metadata['once'] else ''}") # {inspect.getfile(callback_func)}")
                # print(f"  {metadata['name']}() [once={metadata['once']}, raise_error={metadata['raise_error']}]")
            print()
