import inspect
import logging
import re
import sys
from functools import lru_cache, wraps
from threading import Thread, Event
from typing import Iterable, Any, Callable

from agio.core.events import emit
from agio.core.plugins.mixins import BasePluginClass
from agio.core.plugins.plugin_base import APlugin
from agio.core.utils.action_items import ActionItem
from agio.core.utils.text_utils import unslugify

logger = logging.getLogger(__name__)


def get_class_from_method(func):
    if not hasattr(func, "__qualname__") or not hasattr(func, "__module__"):
        return None

    module = sys.modules.get(func.__module__)
    if module is None:
        return None

    class_path = func.__qualname__.split('.<locals>', 1)[0].rsplit('.', 1)[0]
    cls = getattr(module, class_path, None)
    return cls


def action(
        menu_name: str|Iterable[str] = None,
        app_name: str|Iterable[str] = None,
        label: str = None,
        icon: str = None,
        order: int = 50,
        group: str = None,  # TODO not used
        args: Iterable[Any] = None,
        kwargs: dict[str: Any] = None,
        is_visible_callback: Callable = None,
        ):
    if callable(label):
        raise ValueError('The action decorator bust be called')
    if group is not None:
        if not re.fullmatch(r"([\w\s!.]+/?)+", group):
            raise ValueError(f'Wrong action group path "{group}"')
    if isinstance(menu_name, str):
        menu_name = [menu_name]
    if isinstance(app_name, str):
        app_name = [app_name]
    def decorator(func):

        action_data = {
            # filters
            'menu_name': menu_name,
            'app_name': app_name,
            # action properties
            'name': func.__name__,
            'label': label or unslugify(func.__name__),
            'icon': icon,
            'order': order,
            'group': group,
            'kwargs': kwargs or {},
            'args': args or (),
            'action': None,  # updated later in metaclass
            'is_visible_callback': is_visible_callback,
        }

        @wraps(func)
        def wrapper(self, *_args, **_kwargs):
            emit('core.services.call_action', action_data)
            final_kwargs = {**action_data['kwargs'], **_kwargs}
            return func(self, *_args, **final_kwargs)

        wrapper._action_data = action_data
        return wrapper
    return decorator


class _UpdateActions(type):
    def __new__(cls, clsname, bases, attrs):
        if 'name' in attrs:
            service_name = attrs['name']
            for name, func in attrs.items():
                if hasattr(func, '_action_data'):
                    action_full_name = f"{service_name}.{func._action_data['name']}"
                    func._action_data['action'] = action_full_name
        return super().__new__(cls, clsname, bases, attrs)


class ServicePlugin(BasePluginClass, APlugin, metaclass=_UpdateActions):
    plugin_type = 'service'
    menu_name = None
    app_name = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.menu_name is not None:
            if isinstance(self.menu_name, str):
                self.menu_name = [self.menu_name]
        if self.app_name is not None:
            if isinstance(self.app_name, str):
                self.app_name = [self.app_name]

    @property
    def plugin_hub(self):
        from agio.core import plugin_hub
        return plugin_hub

    @property
    def package_hub(self):
        from agio.core import package_hub
        return package_hub

    @property
    def process_hub(self):
        from agio.core import process_hub
        return process_hub

    def before_start(self, **kwargs):
        pass

    def on_stopped(self):
        pass

    def start(self, **kwargs):
        self.before_start(**kwargs)
        self.execute(**kwargs)

    def execute(self, **kwargs):
        raise NotImplementedError

    def stop(self):
        self.on_stopped()

    @lru_cache
    def collect_actions(self):
        items = []
        for name, func in self.__iter_actions__(active_only=True):
            acton_data = getattr(func, '_action_data')
            # action_name = acton_data.get('name') or name
            action_menu_name = acton_data.get('menu_name') or self.menu_name
            if not action_menu_name:
                continue
            # acton_data.update(dict(
            #     label=acton_data.get('label') or unslugify(name),
            #     # action=f"{self.name}.{action_name}",
            # ))
            item_data = {k: v for k, v in acton_data.items() if k in ActionItem.get_fields()}
            emit('core.services.action_item_created', item_data)
            items.append(item_data)
        return items

    def get_action(self, action_name: str):
        for name, func in self.__iter_actions__(active_only=False):
            if name == action_name:
                return func

    def __iter_actions__(self, active_only=False):
        for method, func in self.__iter_methods__():
            if hasattr(func, '_action_data'):
                if active_only and bool(getattr(func, 'menu_name', False)):
                    continue
                yield method, func

    def __iter_methods__(self):
        for name, member in inspect.getmembers(self, predicate=inspect.ismethod):
            if not name.startswith('_'):
                yield name, member


class ThreadServicePlugin(ServicePlugin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._thread = None
        self._event = Event()

    def start(self, **kwargs):
        self.before_start(**kwargs)
        self._thread = Thread(target=self.execute, **kwargs)
        self._thread.start()

    def is_stopped(self):
        return self._event.is_set()

    def stop(self):
        self._event.set()
        if self._thread:
            self._thread.join()
        self.on_stopped()


class ProcessServicePlugin(ServicePlugin):
    process_name = None
    auto_restart = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.process = None

    def execute(self, **kwargs):
        cmd = self.get_startup_command()
        logger.debug(f'Service {self.name} process  cmd: {cmd}')
        self.process = self.process_hub.register_process(
            name=self.process_name,
            command=self.get_startup_command(),
            restart=self.auto_restart,
            cwd=self.get_cwd(),
            env=self.get_env()
        )
        self.process_hub.start_process(self.process_name)
        logger.debug('Process started: %s', self.process_name)

    @action()
    def stop_process(self, hard: bool = True):
        if self.process_hub.is_process_alive(self.process_name):
            self.process_hub.stop_process(self.process_name, hard=hard)
            return True
        return False

    @action()
    def start_process(self, **kwargs):
        if self.process_hub.is_process_alive(self.process_name):
            return False
        self.process_hub.start_process(self.process_name)
        return True

    @action()
    def restart_process(self, **kwargs):
        if self.process_hub.is_process_alive(self.process_name):
            self.process_hub.restart_process(self.process_name)
            return True
        return False

    @action()
    def get_process_info(self, **kwargs):
        if self.process:
            return self.process.info()

    @action()
    def get_process_status(self, **kwargs):
        return self.process_hub.is_process_alive(self.process_name)

    def get_startup_command(self) -> list[str]:
        raise NotImplementedError

    def get_cwd(self) -> str|None:
        return

    def get_env(self) -> dict|None:
        return