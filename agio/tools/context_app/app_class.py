from __future__ import annotations

import os
from functools import cached_property
from typing import Iterable

from agio.core.exceptions import ApiNamespaceConflictError, ApiNamespaceNotExists
from agio.core.plugins import base_app_api
from agio.core.plugins import plugin_hub
from agio.tools import env_names


class ContextApp:
    """
    This class provide API of current application
    """
    def __init__(self):
        self.__is_initialized = False
        self.__namespaces = {}

    @cached_property
    def name(self) -> str:
        return os.getenv(env_names.APP_NAME, 'core')

    @cached_property
    def groups(self) -> set[str]:
        from_env = os.getenv(env_names.APP_GROUPS)
        if from_env:
            return set(from_env.split(','))
        else:
            return {'standalone'}

    @cached_property
    def version(self):
        return os.getenv(env_names.APP_VERSION, '---') # TODO: fix it

    def __collect_namespaces(self):
        plg_hub: plugin_hub.APluginHub = plugin_hub.APluginHub.instance()
        for plg in plg_hub.iter_plugins('application_api'):
            plg: base_app_api.ApplicationAPIBasePlugin
            self.__add_namespace(plg.namespace, plg)
        self.__is_initialized = True

    def __add_namespace(self, namespace: str, obj: base_app_api.ApplicationAPIBasePlugin):
        if namespace not in self.__namespaces:
            self.__namespaces[namespace] = obj
        else:
            current_name = type(self.__namespaces[namespace]).__name__
            new_name = type(obj).__name__
            raise ApiNamespaceConflictError(
                detail=f"API namespace conflict, '{namespace}' already registered. {current_name} > {new_name}"
            )

    def __getattr__(self, item):
        try:
            return self.__get_namespace(item)
        except ApiNamespaceNotExists as e:
            raise AttributeError from e

    def __get_namespace(self, name: str):
        if not self.__is_initialized:
            self.__collect_namespaces()
        if name in self.__namespaces:
            return self.__namespaces[name]
        raise ApiNamespaceNotExists(detail=f"Namespace does not exist, '{name}'")

    def get_namespaces(self):
        if not self.__is_initialized:
            self.__collect_namespaces()
        return tuple(self.__namespaces.keys())

    def print_context(self):
        print(f' App Name: {self.name}')
        print(f'   Groups: {self.groups or "[not set]"}')
        print(f'  Version: {self.version or "[not set]"}')
        if self.__namespaces:
            print('Namespaces:')
            for namespace, obj in self.__namespaces.items():
                print(f'  {namespace} ({obj.__name__})')
        else:
            print('No registered namespaces')

    def is_namespace_registered(self, namespace: str) -> None:
        if namespace not in self.__namespaces:
            raise NameError(f"Namespace '{namespace}' not registered")

    def filter_by_name_and_group(
            self,
            app_names: str|Iterable[str] = None,
            app_groups: str|Iterable[str] = None,
            ) -> bool:
        """Check allowed module by app name and app groups"""
        name_match = grp_match = not any((app_names, app_groups))
        if app_names:
            if isinstance(app_names, (list, tuple)):
                app_names = set(app_names)
            elif isinstance(app_names, str):
                app_names = {app_names}
            if not isinstance(app_names, set):
                raise TypeError("app_names must be a set or a str")
            name_match =  self.name in app_names
        if app_groups:
            if isinstance(app_groups, (list, tuple)):
                app_groups = set(app_groups)
            elif isinstance(app_groups, str):
                app_groups = {app_groups}
            if not isinstance(app_groups, set):
                raise TypeError(f"app_groups must be a set, list or tuple")
            grp_match = bool(self.groups.intersection(app_groups))
        return any([name_match, grp_match])

