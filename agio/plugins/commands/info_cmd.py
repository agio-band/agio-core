import sys

import click


from agio.core.plugins.base.base_plugin_command import ACommand


class InfoCommand(ACommand):
    command_name = 'info'
    arguments = [
        click.option('-g', '--packages', is_flag=True, help='Show packages info', type=bool),
        click.option("-p", "--plugins", is_flag=True, help='Show plugins info.', type=bool),
    ]
    help = 'Show info about current workspace'

    def execute(self, packages, plugins):
        from agio.core.workspace.workspace import AWorkspace

        line = lambda: print('='*70)
        ws = AWorkspace.current()
        line()
        print('Workspace:', ws or '[Not set]', f'[{ws.id if ws else "N/A"}]')
        # print(ws.root.as_posix())
        line()
        print('Python', sys.version)
        # print(ws.venv_manager.python_executable.replace(ws.id, '<ID>'))
        line()
        if any([packages, plugins]):
            if packages:
                self._show_packages_info()
            if plugins:
                self._show_plugins_info()
        else:
            self._show_packages_info()
            self._show_plugins_info()
        line()

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
        for plugin in plugin_hub.iter_plugins():
            print(f"{plugin!r}")
        print()
