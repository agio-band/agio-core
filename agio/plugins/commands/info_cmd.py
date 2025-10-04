import os
import re
import sys
from collections import defaultdict

import click
from pprint import pprint
from agio.core.plugins.base_command import ACommandPlugin
from agio.core.plugins.base_plugin import APlugin
from agio.core.pkg.package import APackageManager
from agio.core.pkg.workspace import AWorkspaceManager
from agio.core.utils import package_hub, plugin_hub
from agio.core.api import client


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
        if not client.ping():
            click.secho('Server not available!', err=True,  fg='red', bg='yellow')
            return
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

        pkg_hub = package_hub.APackageHub.instance()
        print('PACKAGES:')
        print()

        sizes = [len(name) for name in pkg_hub.get_packages().keys()]
        if not sizes:
            raise Exception('No packages found')
        max_len = max(sizes)
        for package in pkg_hub.get_package_list():
            package: APackageManager
            print(f"  {package.package_name:<{max_len+2}} v{package.package_version:<8} | {package.root}")
        print()

    def _show_plugins_info(self):
        plg_hub = plugin_hub.APluginHub.instance()
        print('PLUGINS:')
        print()
        all_plugins_by_package = defaultdict(list)
        for plugin in plg_hub.iter_plugins():
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
        from agio.core.settings import get_local_settings

        local_settings = get_local_settings()
        print('LOCAL SETTINGS:')
        pprint(local_settings)
        print()
        print('WORKSPACE SETTINGS:')
        print('TODO...')

    def show_callbacks(self):
        from agio.core.events import event_hub

        print('CALLBACKS:')
        print()
        event_hub.print_event_list()

    def show_projects_disk_usage(self):
        ...

    def show_libs_disk_usage(self):
        ...


class EnvCommand(ACommandPlugin):
    name = 'env_cmd'
    command_name = 'env'
    help = 'Show agio env'
    arguments = [
        click.option('-p', '--py_envs', is_flag=True, help='Show Python envs'),
    ]

    def execute(self, py_envs, *args, **kwargs):
        keys = [k for k in os.environ.keys() if k.startswith('AGIO_')]
        if py_envs:
            keys.extend([k for k in os.environ.keys() if k.startswith('PYTHON_')])
            keys.append('PATH')
        if not keys:
            print('No AGIO env found')
            return
        max_length = max(len(k) for k in keys)
        for k in keys:
            value = os.environ[k]
            if self.is_multipath(value):
                parts = value.split(':')
                click.secho(f"{k:>{max_length + 2}} = {parts[0]}", fg='green')
                for part in parts[1:]:
                    click.secho(f"{' ':>{max_length + 5}}{part}", fg='green')
            else:
                click.secho(f"{k:>{max_length+2}} = {value}", fg='green')

    def is_multipath(self, value: str) -> bool:
        if os.pathsep not in value:
            return False
        else:
            if value.startswith('http'):
                return False
            return True
