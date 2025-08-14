import logging
from dataclasses import dataclass
from fnmatch import fnmatch
from functools import lru_cache
from typing import Any, Callable

import requests
from agio.core.utils import plugin_hub


logger = logging.getLogger(__name__)
EXECUTE_ACTION_URL = 'http://localhost:8080/action'


@dataclass
class ActionItem:
    action: str
    name: str
    label: str
    icon: str|None
    order: int
    group: str|None
    menu_name: list[str]|None
    app_name: list[str]|None
    args: tuple|list|None
    kwargs: dict|None
    is_visible_callback: Callable|None = None

    def serialize(self) -> dict:
        return {
            'type': 'action',
            'action': self.action,
            'name': self.name,
            'label': self.label,
            'icon': self.icon,
            'order': self.order,
            'group': self.group or '',
            'app_name': self.app_name,
            'args': self.args or [],
            'kwargs': self.kwargs or dict(),
        }

    @classmethod
    def get_fields(cls) -> list:
        return cls.__match_args__

    @property
    def is_visible(self):
        if self.menu_name and self.app_name:
            if self.is_visible_callback:
                return self.is_visible_callback()
            else:
                return True
        return False

    def is_match(self, menu_name: str, app_name: str) -> bool:
        if isinstance(self.menu_name, str):
            current_menu_name = [self.menu_name]
        else:
            current_menu_name = self.menu_name
        if isinstance(self.app_name, str):
            current_app_name = [self.app_name]
        else:
            current_app_name = self.app_name
        return (
            any([fnmatch(name, menu_name) for name in current_menu_name])
            and
            any([fnmatch(name, app_name) for name in current_app_name])
        )

    def __lt__(self, other):
        if not isinstance(other, ActionItem):
            return NotImplemented
        if self.group == other.group:
            return self.order < other.order
        return (self.group or '') < (other.group or '')

    @property
    def plugin_name(self):
        return self.action.split('.')[0]

    @property
    def action_name(self):
        return self.action.split('.')[-1]

    def get_executable(self):

        plugin = plugin_hub.APluginHub.instance().find_plugin_by_name('service', self.plugin_name)
        if not plugin:
            raise RuntimeError(f'Plugin "{self.plugin_name}" not found')
        func = plugin.get_action(self.action_name)
        if not func:
            raise RuntimeError(f'Action "{self.action_name}" not found')
        return func

    def __call__(self, *args, **kwargs):
        func = self.get_executable()
        return func(*self.args, **self.kwargs)


class DividerItem:
    # TODO
    def serialize(self) -> dict:
        return {"type": "divider"}


class ActionGroupItem:
    """Menu or group of items"""
    def __init__(self, name: str|None, label: str|None, items: list = None) -> None:
        self.name = name
        self.label = label
        self._items = []
        if items is not None:
            self.add_items(*items)

    def add_items(self, *items: ActionItem) -> None:
        self._items.extend(items)

    def sorted_items(self) -> list[ActionItem]:
        return sorted(self._items)

    def serialize(self) -> dict:
        return {
            'name': self.name,
            'label': self.label,
            'items': [item.serialize() for item in self.sorted_items()],
            'type': 'group',
            'group': self.name,
        }

    def __repr__(self):
        return f'<{self.__class__.__name__}(name={self.name!r}, items={len(self._items)})>'

    def __str__(self):
        return f'{self.__class__.__name__}(name={self.name!r}, items={len(self._items)})'

    def __bool__(self) -> bool:
        return bool(self._items)

    def __iter__(self):
        return iter(self.sorted_items())


@lru_cache
def get_actions(menu_name: str, app_name: str) -> ActionGroupItem:
    from agio.core.utils import context

    app_name = app_name or context.app_name
    grp = ActionGroupItem(menu_name, None)
    for plugin in plugin_hub.APluginHub.instance().iter_plugins('service'):
        for action_data in plugin.collect_actions():
            action = ActionItem(**action_data)
            if not action.is_match(menu_name, app_name):
                continue
            action.name = f"{plugin.package.package_name}.{action.name}"
            grp.add_items(action)
            # TODO add divider
    return grp

def get_action_func(action_full_name: str) -> Callable:

    service_name, action_name = action_full_name.split('.')
    service = plugin_hub.APluginHub.instance().find_plugin_by_name('service', service_name)
    if not service:
        raise Exception(f'Service {service_name} not found')
    action_func = service.get_action(action_name)
    if not action_func:
        raise Exception(f'Action {action_full_name} not found')
    return action_func