import inspect
import logging
import sys
from fnmatch import fnmatch
from functools import lru_cache
from threading import Thread, Event

from agio.core.actions import action_item, make_action
from agio.core.events import emit
from agio.core.plugins import plugin_hub
from agio.core.plugins.base_plugin import APlugin
from agio.core.workspaces import package_hub
from agio.tools import process_hub
from agio.tools.packaging_tools import version_matches

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


def _match_list(declared, requested: str) -> bool:
    """Match a requested value (fnmatch pattern) against a declared str or list of str"""
    if isinstance(declared, str):
        declared = [declared]
    if not declared:
        return False
    return any(fnmatch(name, requested) for name in declared)


def _match_action_group(declared, requested: str) -> bool:
    """Match action group path: exact, fnmatch pattern or any subgroup of the requested group"""
    if not declared:
        return False
    if declared == requested:
        return True
    if fnmatch(declared, requested):
        return True
    return declared.startswith(f'{requested.strip("/")}/')


class ServicePlugin(APlugin):
    """Base service plugin"""
    plugin_type = 'service'
    menu_name = None
    app_name = None
    app_group = None
    __is_base_plugin__ = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.menu_name is not None:
            if isinstance(self.menu_name, str):
                self.menu_name = [self.menu_name]
        if self.app_name is not None:
            if isinstance(self.app_name, str):
                self.app_name = [self.app_name]
        if self.app_group is not None:
            if isinstance(self.app_group, str):
                self.app_group = [self.app_group]

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        service_name = getattr(cls, 'name', None)
        if service_name:
            for name, func in cls.__dict__.items():
                if hasattr(func, '_action_data'):
                    action_full_name = f"{service_name}.{func._action_data['name']}"
                    func._action_data['action'] = action_full_name

    @property
    def plugin_hub(self):
        return plugin_hub.APluginHub.instance()

    @property
    def package_hub(self):
        return package_hub.APackageHub.instance()

    @property
    def process_hub(self):
        return process_hub.ProcessHub.instance()

    def before_start(self, **kwargs):
        pass

    def on_stopped(self):
        pass

    def start(self, **kwargs):
        self.before_start(**kwargs)
        self.execute(**kwargs)

    def execute(self, **kwargs):
        pass

    def stop(self):
        self.on_stopped()

    @lru_cache
    def collect_actions(
            self,
            hidden: bool = False,
            menu_name: str = None,
            app_name: str = None,
            app_group: str = None,
            app_version: str = None,
            action_group: str = None,
    ) -> list:
        items = []
        for name, func in self.__iter_actions__(visible_only=True):
            action_data = getattr(func, '_action_data')
            if not self._match_action_filters(
                    action_data,
                    hidden=hidden,
                    menu_name=menu_name,
                    app_name=app_name,
                    app_group=app_group,
                    app_version=app_version,
                    action_group=action_group,
            ):
                continue
            item_data = {k: v for k, v in action_data.items() if k in action_item.ActionItem.get_fields()}
            emit('core.services.action_item_created', item_data)
            items.append(item_data)
        return items

    def _match_action_filters(
            self,
            action_data: dict,
            hidden: bool = False,
            menu_name: str = None,
            app_name: str = None,
            app_group: str = None,
            app_version: str = None,
            action_group: str = None,
    ) -> bool:
        """
        Check action data against all passed filters.
        Every passed filter must be satisfied (AND).
        In the app dimension the name or the group can match (OR).
        """
        declared_menu_name = action_data.get('menu_name') or self.menu_name
        if not declared_menu_name and not hidden:
            return False
        if menu_name is not None and not _match_list(declared_menu_name, menu_name):
            return False
        if app_name is not None or app_group is not None:
            name_match = app_name is not None and _match_list(
                action_data.get('app_name') or self.app_name, app_name)
            group_match = app_group is not None and _match_list(
                action_data.get('app_group') or self.app_group, app_group)
            if not (name_match or group_match):
                return False
        if app_version is not None:
            if not version_matches(app_version, action_data.get('app_version')):
                return False
        if action_group is not None:
            if not _match_action_group(action_data.get('group'), action_group):
                return False
        return True

    def get_action(self, action_name: str):
        for name, func in self.__iter_actions__(visible_only=False):
            if name == action_name:
                return func

    def __iter_actions__(self, visible_only=False):
        for method, func in self.__iter_methods__():
            if hasattr(func, '_action_data'):
                if visible_only and bool(getattr(func, 'menu_name', False)):
                    continue
                yield method, func

    def __iter_methods__(self):
        for name, member in inspect.getmembers(self, predicate=inspect.ismethod):
            if not name.startswith('_'):
                yield name, member


class ThreadServicePlugin(ServicePlugin):
    """Threaded service plugin"""
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
    """Subprocess service plugin"""
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

    @make_action()
    def stop_process(self, hard: bool = True):
        if self.process_hub.is_process_alive(self.process_name):
            self.process_hub.stop_process(self.process_name, hard=hard)
            return True
        return False

    @make_action()
    def start_process(self, **kwargs):
        if self.process_hub.is_process_alive(self.process_name):
            return False
        self.process_hub.start_process(self.process_name)
        return True

    @make_action()
    def restart_process(self, **kwargs):
        if self.process_hub.is_process_alive(self.process_name):
            self.process_hub.restart_process(self.process_name)
            return True
        return False

    @make_action()
    def get_process_info(self, **kwargs):
        if self.process:
            return self.process.info()

    @make_action()
    def get_process_status(self, **kwargs):
        return self.process_hub.is_process_alive(self.process_name)

    def get_startup_command(self) -> list[str]:
        raise NotImplementedError

    def get_cwd(self) -> str|None:
        return

    def get_env(self) -> dict|None:
        return