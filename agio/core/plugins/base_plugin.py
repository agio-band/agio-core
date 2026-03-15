from __future__ import annotations

import inspect
import logging
import os
from abc import ABCMeta
from pathlib import Path
from typing import TYPE_CHECKING, Generator

from agio.core.exceptions import PluginLoadingError

from agio.tools.modules import import_module_by_path
from agio.tools.text_helpers import unslugify
if TYPE_CHECKING:
    from agio.core.workspaces.package import APackageManager

logger = logging.getLogger(__name__)


class PluginMeta(ABCMeta):
    def __call__(cls, *args, **kwargs):
        if cls.__dict__.get("__is_base_plugin__", False):
            raise TypeError(f"Creating instance of base plugin class ins not allowed {cls.__name__}")
        return super().__call__(*args, **kwargs)


class APlugin(metaclass=PluginMeta):
    plugin_type = None
    name = None
    required_attrs = None
    __is_base_plugin__ = True

    def __init__(self, package: APackageManager, plugin_info: dict):
        self._plugin_info = plugin_info
        self._package = package # local package tools
        if self.required_attrs:
            for attr in self.required_attrs:
                if getattr(self, attr) is None:
                    raise PluginLoadingError(f'Required attribute "{self.__class__.__name__}.{attr}" must be set.')

    def get_label(self):
        return self._plugin_info.get('label') or unslugify(self.name)

    @property
    def path(self):
        class_file = inspect.getfile(self.__class__)
        return os.path.abspath(class_file)

    def __repr__(self):
        return f'<{self.__class__.__name__} "{self.package.package_name}.{self.name}">'

    def __str__(self):
        return self.name

    @classmethod
    def load_from_info(cls, plugin_info: dict, info_file_path: str) -> Generator[APlugin, None, None]:
        from agio.apps import app

        for imp in plugin_info.get('implementations', ()):
            if not app.filter_by_name_and_group(imp.get('apps'), imp.get('app_groups')):
                continue
            module = imp.get('module')
            if not module:
                raise PluginLoadingError(f"Module is required")
            full_path = Path(info_file_path).parent / module
            logger.debug(f'Load implementation for plugin: {module}')
            if not full_path.exists():
                raise PluginLoadingError(f"Module file not found: {full_path} in {info_file_path}")
            try:
                module_name = module.split('.')[0].replace('/', '.')
                # todo: add from package root
                plugin_module = import_module_by_path(full_path, module_name)
            except Exception as e:
                raise PluginLoadingError(f"Error loading plugin: {full_path} [{e}]") from e

            for obj in plugin_module.__dict__.values():
                if inspect.isclass(obj):
                    if issubclass(obj, APlugin) and not obj.__name__ == APlugin.__name__:
                        if not obj.__dict__.get("__is_base_plugin__"):
                            if obj.__module__ == plugin_module.__name__:
                                if not obj.name:
                                    raise PluginLoadingError(f'{obj.__name__}: plugin name is required ({full_path})')
                                yield obj

    @property
    def package(self):
        return self._package
