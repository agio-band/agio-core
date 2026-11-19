from __future__ import annotations

import os
from functools import cached_property
from typing import Iterable

from agio.apps.ctx import DEFAULT_APP_NAME, get_current_app_groups, match_names_and_groups
from agio.core.exceptions import ApiNamespaceConflictError, ApiNamespaceNotExists
from agio.core.plugins import base_app_api
from agio.core.plugins import plugin_hub
from agio.tools import env_names


class ContextApp:
    """
    This class provide API of current application
    """
    default_name = DEFAULT_APP_NAME

    def __init__(self, variant: str = None):
        self.__is_initialized = False
        self.__namespaces = {}
        self._variant = variant or os.getenv(env_names.APP_VARIANT)

    def __str__(self):
        return self.name

    def __repr__(self):
        return f'<ContextApp name={self.name} version={self.version or "None"} mode={self.mode}>'

    @cached_property
    def parts(self) -> list[str]:
        from agio.apps.app_hub import ApplicationHub
        if self._variant:
            return ApplicationHub.parse_key(self._variant)
        else:
            return self.default_name, None, None

    @property
    def variant(self):
        if self._variant:
            return self._variant
        else:
            return self.default_name

    @cached_property
    def name(self) -> str:
        return self.parts[0]

    @cached_property
    def groups(self) -> set[str]:
        return get_current_app_groups()

    @cached_property
    def version(self):
        return self.parts[1]

    @cached_property
    def mode(self):
        return self.parts[2]

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
        return match_names_and_groups(
            app_names,
            app_groups,
            current_app_name=self.name,
            current_app_groups=self.groups,
        )

    def get_current_app(self):
        from agio.apps import app_hub
        if self.name and self.version:
            return app_hub.get_app(self.name, self.version, self.mode)
        return None