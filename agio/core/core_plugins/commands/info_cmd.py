import click
from agio.core.plugins.plugin_cmd_base import ACommand


class InfoCommand(ACommand):
    command_name = 'info'
    arguments = [
        click.option("-c", "--core", is_flag=True, help='Show core info.', type=bool),
        click.option("-p", "--plugins", is_flag=True, help='Show plugins info.', type=bool),
        click.option('-g', '--packages', is_flag=True, help='Show packages info', type=bool),
    ]

    def execute(self, core, plugins, packages):
        print('='*30)
        if any([core, plugins, packages]):
            if core:
                self._show_core_info()
            if plugins:
                self._show_plugins_info()
            if packages:
                self._show_packages_info()
        else:
            self._show_core_info()
            self._show_plugins_info()
            self._show_packages_info()
        print('=' * 30)

    def _show_core_info(self):
        import agio.core
        print(f"agio-core v{agio.core.__version__}")

    def _show_plugins_info(self):
        print('PLUGINS INFO TODO')

    def _show_packages_info(self):
        print('PACKAGES INFO TODO')
