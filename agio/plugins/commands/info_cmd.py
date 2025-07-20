import sys
from collections import defaultdict

import click
from pprint import pprint
from agio.core.plugins.base_command import ACommandPlugin
from agio.core.plugins.base_plugin import APlugin
from agio.core.pkg.package import APackageManager
from agio.core.pkg.workspace import AWorkspaceManager


class InfoCommand(ACommandPlugin):
    name = 'info_cmd'
    command_name = 'info'
    arguments = [
        click.option('-g', '--packages', is_flag=True, help='Show packages info'),
        click.option("-p", "--plugins", is_flag=True, help='Show plugins info'),
        click.option("-s", "--settings", is_flag=True, help='Show settings'),
        click.option("-c", "--callbacks", is_flag=True, help='Show callbacks'),
        click.option("-d", "--diskusage", is_flag=True, help='Show callbacks'),
    ]
    help = 'Show info about current workspace'

    def execute(self, packages, plugins, settings, callbacks, diskusage):
        line = lambda: print('='*70)
        line()
        self._show_workspace_info()
        line()
        self._show_python_info()
        line()
        if any([packages, plugins, settings, callbacks]):
            if packages:
                self._show_packages_info()
            if plugins:
                self._show_plugins_info()
            if settings:
                self._show_settings()
            if callbacks:
                self.show_callbacks()
        else:
            self._show_packages_info()
            self._show_plugins_info()
            self.show_callbacks()
        line()

    def _show_workspace_info(self):
        ws_manager = AWorkspaceManager.current()
        if ws_manager:
            ws = ws_manager.get_workspace()
            print(f'Workspace: {ws} [{ws.id}]' )
        else:
            print('Workspace: [Not set]')

    def _show_python_info(self):
        print('Python', sys.version)
        print(sys.executable)

    def _show_packages_info(self):
        from agio.core import package_hub
        print('PACKAGES:')
        print()
        for package in package_hub.get_package_list():
            package: APackageManager
            print(f"{package.package_name} v{package.package_version} {package.root}")
        print()

    def _show_plugins_info(self):
        from agio.core import plugin_hub
        print('PLUGINS:')
        print()
        all_plugins_by_package = defaultdict(list)
        for plugin in plugin_hub.iter_plugins():
            plugin: APlugin
            all_plugins_by_package[plugin.package.package_name].append(plugin)
        for package_name, plugins in all_plugins_by_package.items():
            package_plugins = defaultdict(list)
            print(f"[{package_name}]")
            for plugin in plugins:
                package_plugins[plugin.plugin_type].append(plugin)
            for plugin_type, _plugins in package_plugins.items():
                print(f"  {plugin_type}:")
                for plugin in _plugins:
                    print(f"    {plugin.name}")
            print()
        print()

    def _show_settings(self):
        from agio import local_settings, workspace_settings
        print('LOCAL SETTINGS:')
        pprint(local_settings)
        print()
        print('WORKSPACE SETTINGS:')
        pprint(workspace_settings)

    def show_callbacks(self):
        from agio.core.events import event_hub

        print('CALLBACKS:')
        print()
        event_hub.print_event_list()

    def show_projects_disk_usage(self):
        ...

    def show_libs_disk_usage(self):
        ...
