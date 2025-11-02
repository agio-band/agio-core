from __future__ import annotations

import inspect
import os
import sys
from collections import defaultdict
from pathlib import Path
from typing import TYPE_CHECKING

import click
from pprint import pprint
from agio.core.plugins.base_command import ACommandPlugin, ASubCommand
from agio.core.plugins.base_plugin import APlugin
from agio.core.workspaces.package import APackageManager
from agio.core.workspaces.workspace import AWorkspaceManager
from agio.core.plugins import plugin_hub
from agio.core.workspaces import package_hub
from agio.core.api import client, profile
if TYPE_CHECKING:
    from agio.core.settings.settings_hub import LocalSettingsHub



class EnvInfoCommand(ASubCommand):
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


class PackagesInfoCommand(ASubCommand):
    command_name = 'packages'

    def execute(self, *args, **kwargs):
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
            print(f"  {package.package_name:<{max_len+2}} {package.package_version:<8}")# | {strip_path(package.root)}")


class WorkspacesInfoCommand(ASubCommand):
    command_name = 'ws'

    def execute(self, *args, **kwargs):
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
            print('Name: [default]')
            print('ID: [none]')
            print(f'Root: {Path(sys.executable).parent.parent.parent}')


class SettingsInfoCommand(ASubCommand):
    command_name = 'settings'

    def execute(self, *args, **kwargs):
        from agio.core import settings

        local_settings: LocalSettingsHub = settings.get_local_settings()
        print('Settings file: ',end='')
        click.secho('TODO',fg='magenta')
        pprint(local_settings.dump())


class PluginsInfoCommand(ASubCommand):
    command_name = 'plugins'

    def execute(self, *args, **kwargs):
        plg_hub = plugin_hub.APluginHub.instance()
        all_plugins_by_package = defaultdict(list)
        for plugin in plg_hub.iter_plugins():
            plugin: APlugin
            all_plugins_by_package[plugin.package.package_name].append(plugin)
        for package_name, plugins in all_plugins_by_package.items():
            package_plugins = defaultdict(list)
            click.secho(f"{package_name}", bold=True, fg='green')
            for plugin in plugins:
                package_plugins[plugin.plugin_type].append(plugin)
            for plugin_type, _plugins in package_plugins.items():
                click.secho(f"  {plugin_type}:", fg='yellow')
                for plugin in _plugins:
                    print(f"    {plugin.name}")
            print()


class CallbacksInfoCommand(ASubCommand):
    command_name = 'callbacks'

    def execute(self, *args, **kwargs):
        from agio.core.events import event_hub

        if not event_hub._callbacks:
            print("No events registered.")
            return

        for event_name in event_hub._callbacks:
            click.secho(f"{event_name}", bold=True, fg="green")
            if not event_hub._callbacks[event_name]:
                print("  (No callbacks)")
                continue
            for callback_func, metadata in event_hub._callbacks[event_name].items():
                click.secho(f"  {metadata['name']}{' [once]' if metadata['once'] else ''}", fg="yellow", nl=False)
                print(f' [{inspect.getfile(callback_func).split("site-packages")[-1]}]')
            print()


class ActionsInfoCommand(ASubCommand):
    command_name = 'actions'

    def execute(self, *args, **kwargs):
        from agio.core.actions import get_all_actions

        for act in get_all_actions():
            click.secho(f"{act.label}", bold=True, fg='green')
            click.secho(f"  name: ", nl=False, fg='yellow')
            click.secho(act.name)
            click.secho( '  menu: ', nl=False, fg='yellow')
            if isinstance(act.menu_name, str):
                menu = act.menu_name
            elif isinstance(act.menu_name, list):
                menu = ', '.join(act.menu_name)
            else:
                menu = '*'
            click.secho(menu)
            click.secho( '  app:  ', nl=False, fg='yellow')
            if isinstance(act.app_name, str):
                app = act.app_name
            elif isinstance(act.app_name, list):
                app = ', '.join(act.app_name)
            else:
                app = '*'
            click.secho(app)


class PythonInfoCommand(ASubCommand):
    command_name = 'python'

    def execute(self, *args, **kwargs):
        print('Version:', sys.version)
        print('Executable:', sys.executable)
        print('\nsys.path:')
        for path in sys.path:
            print('  ', path)


class DiskInfoCommand(ASubCommand):
    command_name = 'disk'

    def execute(self, *args, **kwargs):
        click.secho('TODO', fg='yellow')


class InfoCommand(ACommandPlugin):
    name = 'info_cmd'
    command_name = 'info'
    help = 'System details'

    subcommands = (
        EnvInfoCommand,
        PackagesInfoCommand,
        WorkspacesInfoCommand,
        SettingsInfoCommand,
        PluginsInfoCommand,
        CallbacksInfoCommand,
        ActionsInfoCommand,
        PythonInfoCommand,
        DiskInfoCommand,
    )

    allow_empty_root_command = True
    execute_root_command_before_subcommand = False

    def execute(self, *args, **kwargs):
        user_profile = profile.get_current_user()
        click.echo(f'URL: {client.platform_url}')
        click.echo(f'User: {user_profile["firstName"]} {user_profile["lastName"]}')
        click.echo(f'Email: {user_profile["email"]}')
        #TODO installation path
