import re
from functools import wraps
from typing import Any, Callable, Iterable

from packaging.specifiers import InvalidSpecifier, SpecifierSet

from ..events import emit
from ...tools import text_helpers


def make_action(
        menu_name: str|Iterable[str] = None,
        app_name: str|Iterable[str] = None,
        app_group: str|Iterable[str] = None,
        app_version: str|Iterable[str] = None,
        label: str = None,
        icon: str = None,
        order: int = 50,
        action_group: str = None,
        args: Iterable[Any] = None,
        kwargs: dict[str, Any] = None,
        is_visible_callback: Callable = None,
        ):
    """
    Decorator for service actions.

    Filters (used to select actions, combined with AND):
    :param menu_name: menu name or list of menu names
    :param app_name: app name or list of app names
    :param app_group: app group or list of app groups (alternative to app_name)
    :param app_version: version requirement in PEP 440 format,
        for example ">=10,<15" or [">=10", "<15"].
        None means any version
    :param action_group: group path of the action
    """
    if callable(label):
        raise ValueError('The action decorator bust be called')
    if action_group is not None:
        if not re.fullmatch(r"([\w\s!.]+/?)+", action_group):
            raise ValueError(f'Wrong action group path "{action_group}"')
    if app_version is not None and not isinstance(app_version, str):
        app_version = ','.join(app_version)
    if app_version is not None:
        try:
            SpecifierSet(app_version)
        except InvalidSpecifier as e:
            raise ValueError(f'Wrong app version requirement "{app_version}"') from e
    if isinstance(menu_name, str):
        menu_name = [menu_name]
    if isinstance(app_name, str):
        app_name = [app_name]
    if isinstance(app_group, str):
        app_group = [app_group]

    def decorator(func):

        action_data = {
            # filters
            'menu_name': menu_name,
            'app_name': app_name,
            'app_group': app_group,
            'app_version': app_version,
            # action properties
            'name': func.__name__,
            'label': label or text_helpers.unslugify(func.__name__),
            'icon': icon,
            'order': order,
            'group': action_group,
            'kwargs': kwargs or {},
            'args': args or (),
            'action': None,  # will update later in metaclass
            'is_visible_callback': is_visible_callback,
            # 'user_groups': []  # access permissions on frontend
        }

        @wraps(func)
        def wrapper(self, *_args, **_kwargs):
            emit('core.services.call_action', action_data)
            final_kwargs = {**action_data['kwargs'], **_kwargs}
            return func(self, *_args, **final_kwargs)

        wrapper._action_data = action_data
        return wrapper
    return decorator
