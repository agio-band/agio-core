from functools import lru_cache
from typing import Callable, Iterator

import requests

from .action_item import ActionGroupItem, ActionItem
from ..plugins import plugin_hub


@lru_cache
def get_actions(menu_name: str, app_name: str) -> ActionGroupItem:
    from agio.tools import context

    app_name = app_name or context.app_name
    grp = ActionGroupItem(menu_name, None)
    for action in iter_actions():
        if not action.is_match(menu_name, app_name):
            continue
        grp.add_items(action)
        # TODO add divider
    return grp


def get_all_actions(hidden: bool = True) -> list[ActionItem]:
    return list(iter_actions(hidden))


def iter_actions(hidden: bool = True) -> Iterator[ActionItem]:
    for plugin in plugin_hub.APluginHub.instance().iter_plugins('service'):
        for action_data in plugin.collect_actions(hidden=hidden):
            action = ActionItem(package_name=plugin.package.package_name, **action_data)
            action.name = f"{plugin.name}.{action.name}"
            yield action


def get_action_func(action_full_name: str) -> Callable:

    service_name, action_name = action_full_name.split('.')
    service = plugin_hub.APluginHub.instance().find_plugin_by_name('service', service_name)
    if not service:
        raise Exception(f'Service {service_name} not found')
    action_func = service.get_action(action_name)
    if not action_func:
        raise Exception(f'Action {action_full_name} not found')
    return action_func


def execute_action(action_name, *args, **kwargs):
    action_func = get_action_func(action_name)
    return action_func(*args, **kwargs)


def send_action(action_name, *args, **kwargs):
    url = 'http://127.0.0.1:8877/action'
    data = {
        'action': action_name,
        'kwargs': kwargs,
        'args': args,
    }
    return requests.post(url, json=data, timeout=1).json()