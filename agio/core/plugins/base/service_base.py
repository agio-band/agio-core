import inspect
import re
from threading import Thread, Event
from typing import Callable

from agio.core.events import emit
from agio.core.plugins.mixins import BasePluginClass
from agio.core.plugins.plugin_base import APlugin
from agio.core.utils.text_utils import unslugify


def action(
        add_to_menu: bool = False,
        menu_name: str = None,
        app_name: str = None,
        label: str = None,
        icon: str = None,
        order: int = 50,
        group: str = None,
        ):
    if callable(label):
        raise ValueError('The action decorator bust be called')
    if group is not None:
        if not re.fullmatch(r"([\w\s!.]+/?)+", group):
            raise ValueError(f'Wrong action group path "{group}"')
    def decorator(func):
        func._action_data = {
            'add_to_menu': add_to_menu,
            'menu_name': menu_name,
            'app_name': app_name,
            'name': func.__name__,
            'label': label or unslugify(func.__name__),
            'icon': icon,
            'order': order,
            'group': group,
        }
        return func
    return decorator


class ServicePlugin(BasePluginClass, APlugin):
    plugin_type = 'service'
    menu_name = None
    app_name = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._thread = None
        self._event = Event()

    def start(self, in_thread: bool = True, **kwargs):
        if in_thread:
            self._thread = Thread(target=self.execute, **kwargs)
            self._thread.start()
        else:
            self.execute(**kwargs)

    def is_stopped(self):
        return self._event.is_set()

    def execute(self, **kwargs):
        raise NotImplementedError

    def stop(self):
        self._event.set()
        if self._thread:
            self._thread.join()

    def get_action_items(self, menu_name: str, app_name: str):
        if self.menu_name is not None:
            if menu_name != menu_name:
                return
        if self.app_name is not None:
            if app_name != app_name:
                return
        return self.collect_actions(menu_name, app_name)

    def collect_actions(self, menu_name: str, app_name: str):
        items = []
        for name, func in self.__iter_actions__(active_only=True):
            acton_data = getattr(func, '_action_data')
            action_name = acton_data.get('name') or name
            action_menu_name = acton_data.get('menu_name') or self.menu_name
            if action_menu_name is None:
                raise NameError(f'Menu name is not defined for action {action_name}')
            acton_data.update(dict(
                label=acton_data.get('label') or unslugify(name),
                action=f"{self.name}.{action_name}",
            ))
            items.append(acton_data)
            emit('agio-core.services.action-added',
                 {'menu_name': menu_name, 'action_data': acton_data, 'app_name': app_name})
        return items

    def get_action(self, action_name: str):
        for name, func in self.__iter_actions__(active_only=False):
            if name == action_name:
                return func

    def __iter_actions__(self, active_only=False):
        for method, func in self.__iter_methods__():
            if hasattr(func, '_action_data'):
                if active_only and getattr(func, 'add_to_menu', False):
                    continue
                yield method, func

    def __iter_methods__(self):
        for name, member in inspect.getmembers(self, predicate=inspect.ismethod):
            if not name.startswith('_'):
                yield name, member