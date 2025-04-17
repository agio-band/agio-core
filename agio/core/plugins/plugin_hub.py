import logging
from agio.core.packages.package import APackage
from agio.core.plugins.plugin_base import APlugin
from agio.core.utils.singleton import Singleton

logger = logging.getLogger(__name__)

class APluginHub(metaclass=Singleton):
    def __init__(self, package_hub):
        self.plugins = {}
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
                if plugin.name in self.plugins:
                    if plugin in self.plugins.values():
                        continue
                    logger.warning(f"Plugin {plugin.name} will be overridden by: {plugin}")
                    self._overridden_plugins.append(plugin.name)
                self.plugins[plugin.name] = plugin

    def get_plugins_by_type(self, type_name: str) -> dict[str, 'APlugin']:
        for plugin in self.plugins.values():
            if plugin.plugin_type == type_name:
                yield plugin

    def get_plugin_by_name(self, name: str) -> 'APlugin':
        for plugin in self.plugins.values():
            if plugin.name == name:
                return plugin

    def plugin_exists(self, name: str) -> bool:
        return name in self.plugins

    def iter_loaded_plugins(self):
        for plugin in self.plugins.values():
            yield plugin

    def get_plugins_info(self) -> dict:
        pass



