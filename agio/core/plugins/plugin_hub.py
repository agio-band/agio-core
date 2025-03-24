from agio.core.packages.package_base import APackage
from agio.core.plugins.plugin_base import APlugin
from agio.core.utils.singleton import Singleton


class APluginHub(metaclass=Singleton):
    def __init__(self, package_hub):
        self.plugins = {}
        self.collect_plugins(package_hub.get_package_list())

    def collect_plugins(self, packages: list[APackage]) -> None:
        for pkg in packages:
            for plugin in pkg.collect_plugins():
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

    def get_plugins_info(self) -> dict:
        pass



