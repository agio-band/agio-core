import logging
from collections import defaultdict

from agio.core.packages.package import APackage
from agio.core.plugins.plugin_base import APlugin
from agio.core.utils.singleton import Singleton

logger = logging.getLogger(__name__)

class APluginHub(metaclass=Singleton):
    def __init__(self, package_hub):
        self.plugins = defaultdict(dict)
        self._overridden_plugins = []
        self.package_hub = package_hub

    def collect_plugins(self):
        self._collect_plugins(self.package_hub.get_package_list())

    @property
    def plugins_count(self):
        return len(self.plugins)

    def _collect_plugins(self, packages: list[APackage]) -> None:
        for pkg in packages:
            for plugin in pkg.collect_plugins():
                if not plugin.name:
                    raise ValueError(f"Plugin name must be defined: {plugin}")

                if plugin.name in self.plugins[plugin.plugin_type]:
                    if plugin in self.plugins[plugin.plugin_type].values():
                        continue
                    existing_plugin = self.plugins[plugin.plugin_type][plugin.name]
                    logger.warning(f"Plugin will be overridden by: {plugin.__class__.__name__}.{plugin.name} => {plugin.__class__.__name__}.{existing_plugin.name}")
                    self._overridden_plugins.append(f'{plugin.plugin_type}.{plugin.name}')
                self.plugins[plugin.plugin_type][plugin.name] = plugin

    def get_plugins_by_type(self, type_type: str) -> dict[str, 'APlugin']:
        yield from self.plugins[type_type].values()

    def get_plugin_by_name(self, plugin_type: str, name: str) -> 'APlugin':
        if plugin_type not in self.plugins:
            raise ValueError(f"Plugin type '{plugin_type}' is not defined")
        for plugin in self.plugins[plugin_type].values():
            if plugin.name == name:
                return plugin

    def plugin_exists(self, plugin_type: str, name: str) -> bool:
        if plugin_type not in self.plugins:
            raise ValueError(f"Plugin type '{plugin_type}' is not defined")
        return name in self.plugins[plugin_type]

    def iter_plugins(self):
        for plugins in self.plugins.values():
            for plugin in plugins.values():
                yield plugin

    def get_plugins_info(self) -> dict:
        pass



