from __future__ import annotations
import os
import sys
from collections import defaultdict
from pathlib import Path
from typing import TYPE_CHECKING

import click
from pprint import pprint
from agio.core.plugins.base_command import ACommandPlugin
from agio.core.plugins.base_plugin import APlugin
from agio.core.pkg.package import APackageManager
from agio.core.pkg.workspace import AWorkspaceManager
from agio.core.utils import package_hub, plugin_hub
from agio.core.api import client
if TYPE_CHECKING:
    from agio.core.utils.settings_hub import LocalSettingsHub


def line(caption: str = None, width=80, color=None, padding=True):
    if caption is None:
        if padding:
            print()
        click.secho('='*width, fg=color)
        if padding:
            print()
    else:
        if padding:
            print()
        click.secho(f"=== {caption+ ' ':=<{width-4}}", fg=color)
        if padding:
            print()


class InfoCommand(ACommandPlugin):
    name = 'info_cmd'
    command_name = 'info'
    # arguments = [
    #     click.option('-g', '--packages', is_flag=True, help='Show packages info'),
    #     click.option("-p", "--plugins", is_flag=True, help='Show plugins info'),
    #     click.option("-s", "--settings", is_flag=True, help='Show settings'),
    #     click.option("-c", "--callbacks", is_flag=True, help='Show callbacks'),
    #     click.option("-d", "--diskusage", is_flag=True, help='Show callbacks'),
    # ]
    help = 'Show info about current workspace'

    def execute(self):
        if not client.ping():
            click.secho('Server not available!', err=True,  fg='red', bg='yellow')
            return
        self.show_platform_info()
        self.show_workspace_info()
        self.show_settings()
        self.show_packages_info()
        self.show_plugins_info()
        self.show_callbacks()
        self.show_python_info()
        self.show_libs_disk_usage()
        line(color='yellow')

    def show_platform_info(self):
        line('Platform', color='yellow')
        click.echo(f'URL: {client.platform_url}')

    def show_workspace_info(self):
        line('Workspace', color='yellow')
        ws_manager = AWorkspaceManager.current()
        if ws_manager:
            ws = ws_manager.get_workspace()
            print(f'Name: {ws.name}')
            print(f'ID: {ws.id}')
            root = ws.get_manager().root
            print(f'Root: {root}')
            revisions = list(root.glob('*'))
            if revisions:
                print(f'Revisions: [{len(revisions)}]')
                for rev in revisions:
                    print('  ',rev.name)
        else:
            print('Name: default')
            print('ID: [none]')
            print(f'Root: {Path(sys.executable).parent.parent}')

    def show_python_info(self):
        line('Python', color='yellow')
        print('Version:', sys.version)
        print('Executable:', sys.executable)
        print('sys.path list')
        for path in sys.path:
            print(path)

    def show_packages_info(self):
        line('Packages', color='yellow')
        pkg_hub = package_hub.APackageHub.instance()
        ws_manager = AWorkspaceManager.current()

        sizes = [len(name) for name in pkg_hub.get_packages().keys()]
        if not sizes:
            raise Exception('No packages found')
        max_len = max(sizes)
        def strip_path(path):
            if ws_manager:
                rel = Path(path).relative_to(ws_manager.install_root)
                return f'[WORKSPACE]/{rel}'
            else:
                return path
        for package in pkg_hub.get_package_list():
            package: APackageManager
            print(f"  {package.package_name:<{max_len+2}} v{package.package_version:<8} | {strip_path(package.root)}")

    def show_plugins_info(self):
        line('Plugins', color='yellow')
        plg_hub = plugin_hub.APluginHub.instance()
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

    def show_settings(self):
        from agio.core import settings

        line('Local Settings', color='yellow')
        local_settings: LocalSettingsHub = settings.get_local_settings()
        print('Settings file: ',end='')
        click.secho('TODO',fg='magenta')
        pprint(local_settings.dump())
        line('Workspace Settings', color='yellow')
        click.secho('TODO...', fg='magenta')

    def show_callbacks(self):
        from agio.core.events import event_hub

        line('Callbacks', color='yellow')
        event_hub.print_event_list()

    def show_libs_disk_usage(self):
        line('Libs Disk Usage', color='yellow')
        click.secho('TODO...', fg='magenta')


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
