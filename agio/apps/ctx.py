"""
Helpers of the current application context.
"""
from __future__ import annotations

import os
from typing import Iterable

from agio.tools import env_names

DEFAULT_APP_NAME = 'standalone'


def get_current_app_name() -> str:
    """Return the name part of the current app variant (see AGIO_APP_VARIANT)"""
    variant = os.getenv(env_names.APP_VARIANT)
    if not variant:
        return DEFAULT_APP_NAME
    return variant.partition('/')[0]


def get_current_app_groups() -> set[str]:
    """Return groups of the current app (see AGIO_APP_GROUPS)"""
    from_env = os.getenv(env_names.APP_GROUPS)
    if from_env:
        return set(from_env.split(','))
    return {DEFAULT_APP_NAME}


def match_names_and_groups(
        app_names: str | Iterable[str] = None,
        app_groups: str | Iterable[str] = None,
        current_app_name: str = None,
        current_app_groups: Iterable[str] = None,
        ) -> bool:
    """Check if the current app matches the given name and group filters"""

    def match_lists(to_check: set, match_with: set) -> bool:
        neg_match = {item for item in to_check if item.startswith('!')}
        pos_match = to_check.difference(neg_match)
        neg_match = {item.strip('!') for item in neg_match}
        return bool(pos_match.intersection(match_with) and not neg_match.intersection(match_with))

    def fix_type(value):
        if isinstance(value, (list, tuple)):
            value = set(value)
        elif isinstance(value, str):
            value = {value}
        if not isinstance(value, set):
            raise TypeError(f"value must be a set or a str, not {type(value)}")
        return value

    current_app_name = current_app_name or DEFAULT_APP_NAME
    current_app_groups = set(current_app_groups or ())
    name_match = grp_match = not any((app_names, app_groups))
    if app_names:
        name_match = match_lists(fix_type(app_names), {current_app_name})
    if app_groups:
        grp_match = match_lists(fix_type(app_groups), current_app_groups)
    return any([name_match, grp_match])


def filter_by_name_and_group(
        app_names: str | Iterable[str] = None,
        app_groups: str | Iterable[str] = None,
        ) -> bool:
    """Check allowed module by name and groups of the current app"""
    return match_names_and_groups(
        app_names,
        app_groups,
        current_app_name=get_current_app_name(),
        current_app_groups=get_current_app_groups(),
    )
