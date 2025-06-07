from __future__ import annotations

import inspect, os
from abc import ABC
from pathlib import Path
from typing import TYPE_CHECKING, Generator
import logging
from agio.core.utils.import_utils import import_module_by_path
from agio.core.utils.text_utils import unslugify

if TYPE_CHECKING:
    from agio.core.packages.package import APackage


logger = logging.getLogger(__name__)

class _APluginAbstract(ABC):
    plugin_type = None
    name = None
    is_abstract = True


class APlugin(_APluginAbstract):
    name = None
    label = None

    def __init__(self, package: APackage, plugin_info: dict):
        self._plugin_info = plugin_info
        self.before_load()
        self._package = package
        self.on_load()

    def get_label(self):
        return self.label or unslugify(self.name)

    def __repr__(self):
        return f"{self.package.name}.{self.name}"

    def __str__(self):
        return self.name

    @classmethod
    def load_from_info(cls, plugin_info: dict, manifest_file_path: str) -> Generator[APlugin, None, None]:
        from agio.core.main import app_context
        for imp in plugin_info.get('implementations', ()):
            if supported_apps := imp.get('apps'):
                if isinstance(supported_apps, str):
                    supported_apps = (supported_apps,)
                if not isinstance(supported_apps, (list, tuple, set)):
                    raise ValueError(f"Supported apps must be a iterable [{manifest_file_path}]")
                if app_context.app_name not in supported_apps:
                    logger.debug(f'Skip implementation for {supported_apps}')
                    continue
            if supported_app_groups := plugin_info.get('app_groups'):
                if isinstance(supported_app_groups, str):
                    supported_app_groups = (supported_app_groups,)
                if not isinstance(supported_app_groups, (list, tuple, set)):
                    raise ValueError(f"Supported app groups must be a iterable [{manifest_file_path}]")
                if app_context.app_group not in supported_app_groups:
                    logger.debug(f'Skip implementation for {supported_app_groups}')
                    continue
            module = imp.get('module')
            if not module:
                raise ValueError(f"Module is required")
            full_path = Path(manifest_file_path).parent / module
            logger.debug(f'Load implementation for plugin: {module}')
            if not full_path.exists():
                raise ValueError(f"Module file not found: {full_path}")
            try:
                module_name = module.split('.')[0].replace('/', '.')
                # todo: add from package root
                plugin_module = import_module_by_path(full_path, module_name)
            except Exception as e:
                raise ValueError(f"Error loading plugin: {full_path}") from e
            for obj in plugin_module.__dict__.values():
                if inspect.isclass(obj):
                    if issubclass(obj, APlugin) and not obj.__name__ == APlugin.__name__:
                        if not getattr(obj, 'is_base_class', True):
                            if obj.__module__ == plugin_module.__name__:
                                if not obj.name:
                                    raise ValueError(f'Plugin name is required: {full_path}')
                                yield obj

    @property
    def package(self):
        return self._package

    @property
    def path(self):
        file = inspect.getfile(self.__class__)
        return os.path.abspath(file)

    def before_load(self):
        ...

    def on_load(self):
        ...
