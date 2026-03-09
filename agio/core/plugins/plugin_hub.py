from __future__ import annotations

import logging
import sys
from collections import defaultdict
from typing import Iterator, TYPE_CHECKING, Generator

from agio.core.events import emit
from agio.core.exceptions import PluginLoadingError, PluginNotFoundError
from agio.tools.singleton import Singleton

if TYPE_CHECKING:
    from agio.core.workspaces.package_hub import APackageHub
    from agio.core.workspaces import APackageManager
    from agio.core.plugins.base_plugin import APlugin


logger = logging.getLogger(__name__)


class APluginHub(metaclass=Singleton):
    def __init__(self, package_hub: APackageHub):
        self.plugins = defaultdict(dict)
        self._overridden_plugins = []
        self.package_hub = package_hub

    def collect_plugins(self):
        self._collect_plugins(self.package_hub.get_package_list())

    @property
    def plugins_count(self):
        return sum([len(types) for types in self.plugins.values()])

    def _collect_plugins(self, packages: list[APackageManager]) -> None:
        if self.plugins:
            logger.debug(f"PluginHub already initialized or in progress...")
            return
        for pkg in packages:
            for plugin in pkg.collect_plugins():
                if not plugin.__class__.__dict__.get('name'):
                    raise PluginLoadingError(f"Plugin name must be defined: {plugin.__class__.__name__}")
                if plugin.name in self.plugins[plugin.plugin_type]:
                    if plugin in self.plugins[plugin.plugin_type].values():
                        logger.debug(f"Plugin {plugin.plugin_type}.{plugin.name} already loaded.")
                        continue
                    existing_plugin = self.plugins[plugin.plugin_type][plugin.name]
                    m1 = sys.modules.get(plugin.__class__.__module__)
                    m2 = sys.modules.get(existing_plugin.__class__.__module__)
                    logger.warning(
                        f"Plugin will be overridden by: "
                            f"\nOLD: {m1.__file__}:{plugin.__class__.__name__} ({plugin.name})"
                            f"\nNEW: {m2.__file__}:{existing_plugin.__class__.__name__} ({existing_plugin.name})")
                    self._overridden_plugins.append(f'{plugin.plugin_type}.{plugin.name}')
                self.plugins[plugin.plugin_type][plugin.name] = plugin
                emit('core.app.plugin_loaded', {'plugin': plugin, 'package': pkg})
        logger.debug(f'Plugin hub initialized with {len(self.plugins)} categories')

    def collect_chips(self):
        for pkg in self.package_hub.get_package_list():
            pkg.collect_chips()

    def get_plugins_by_type(self, type_type: str) -> Generator[APlugin, None, None]:
        yield from self.plugins[type_type].values()

    def get_plugin_by_name(self, plugin_type: str, name: str) -> 'APlugin | None':
        if plugin_type not in self.plugins:
            raise PluginNotFoundError(f"Plugin type '{plugin_type}' is not defined")
        for plugin in self.plugins[plugin_type].values():
            if plugin.name == name:
                return plugin
        return None

    def find_plugin_by_name(self, plugin_type: str, name: str) -> 'APlugin|None':
        for plugin in self.plugins[plugin_type].values():
            if plugin.name == name:
                return plugin
        return None

    def plugin_exists(self, plugin_type: str, name: str) -> bool:
        if plugin_type not in self.plugins:
            raise PluginNotFoundError(f"Plugin type '{plugin_type}' is not defined")
        return name in self.plugins[plugin_type]

    def iter_plugins(self, plugin_type: str = None) -> Iterator['APlugin']:
        for _plugin_pype, plugins in self.plugins.items():
            if plugin_type is not None and _plugin_pype != plugin_type:
                continue
            for plugin in plugins.values():
                yield plugin




