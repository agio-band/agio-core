import sys
import click
from pprint import pprint
from agio.core.plugins.base.command_base import ACommandPlugin


class InfoCommand(ACommandPlugin):
    name = 'info_command'
    command_name = 'info'
    arguments = [
        click.option('-g', '--packages', is_flag=True, help='Show packages info'),
        click.option("-p", "--plugins", is_flag=True, help='Show plugins info'),
        click.option("-s", "--settings", is_flag=True, help='Show settings'),
        click.option("-c", "--callbacks", is_flag=True, help='Show callbacks'),
    ]
    help = 'Show info about current workspace'

    def execute(self, packages, plugins, settings, callbacks):
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
        from agio.core.workspace.workspace import AWorkspace
        ws = AWorkspace.current()
        if ws:
            print(f'Workspace: {ws} [{ws.id}]' )
        else:
            print('Workspace: [Not set]')

    def _show_python_info(self):
        print('Python', sys.version)
        print(sys.executable)

    def _show_packages_info(self):
        from agio.core.main import package_hub
        print('PACKAGES:')
        print()
        for package in package_hub.get_package_list():
            print(f"{package.name} v{package.version}")
        print()

    def _show_plugins_info(self):
        from agio.core.main import plugin_hub
        print('PLUGINS:')
        print()
        all_plugins = sorted(
            list(plugin_hub.iter_plugins()),
            key=lambda p: (p.plugin_type, p.name))
        for plugin in all_plugins:
            print(f"{plugin.name}")
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
