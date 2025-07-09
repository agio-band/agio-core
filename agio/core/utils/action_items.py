import logging
from dataclasses import dataclass
from fnmatch import fnmatch
from functools import lru_cache, partial
from typing import Callable, Any
import requests

logger = logging.getLogger(__name__)

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
    callable: Callable|None

    def serialize(self) -> dict:
        return {
            'type': 'item',
            'action': self.action,
            'name': self.name,
            'label': self.label,
            'icon': self.icon,
            'order': self.order,
            'group': self.group or '',
            'app_name': self.app_name,
            'args': self.args or tuple(),
            'kwargs': self.kwargs or dict(),
        }

    @classmethod
    def get_fields(cls) -> list:
        return cls.__match_args__

    @property
    def is_visible(self):
        return self.menu_name and self.app_name

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
        return sorted(self._items)#, key=lambda item: (item.group or '', item.order))

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
    from agio.core import plugin_hub
    from agio.core.utils import context

    app_name = app_name or context.app_name
    grp = ActionGroupItem(None, None)
    for plugin in plugin_hub.iter_plugins('service'):
        for action_data in plugin.collect_actions():
            action = ActionItem(**action_data)
            if not action.is_visible:
                continue
            if not action.is_match(menu_name, app_name):
                continue
            action.name = f"{plugin.package.name}.{action.name}"
            grp.add_items(action)
            # TODO add divider
    return grp


def make_callback(action: ActionItem|dict) -> Callable[..., None]:
    if action.callable:
        logger.debug('Use callable for action: %s', action.name)
        return partial(action.callable, *action.args, **action.kwargs)
    else:
        logger.debug('Use localhost call for action: %s', action.name)
        return partial(call_action, action)


def call_action(action: ActionItem|dict) -> Any:
    data = dict(
        action_name=action.action,
        kwargs=action.kwargs,
        args=action.args,
    )
    resp = requests.post('http://localhost:8080/action', json=data)
    resp.raise_for_status()
    return resp.json()
