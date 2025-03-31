import click


from agio.core.plugins.plugin_cmd_base import ACommand


class InfoCommand(ACommand):
    command_name = 'info'
    arguments = [
        click.option("-c", "--core", is_flag=True, help='Show core info.', type=bool),
        click.option('-g', '--packages', is_flag=True, help='Show packages info', type=bool),
        click.option("-p", "--plugins", is_flag=True, help='Show plugins info.', type=bool),
    ]
    help = 'Show info about current workspace'

    def execute(self, core, packages, plugins):
        print('='*30)
        if any([core, packages, plugins]):
            if core:
                self._show_core_info()
            if packages:
                self._show_packages_info()
            if plugins:
                self._show_plugins_info()
        else:
            self._show_core_info()
            self._show_packages_info()
            self._show_plugins_info()
        print('=' * 30)

    def _show_core_info(self):
        import agio.core

        print(f"Core v{agio.core.__version__}")
        print()

    def _show_packages_info(self):
        from agio.core.init_core import package_hub
        print('PACKAGES:')
        print()
        for package in package_hub.get_package_list():
            print(f"{package.name} v{package.version}")
        print()

    def _show_plugins_info(self):
        from agio.core.init_core import plugin_hub
        print('PLUGINS:')
        print()
        for plugin in plugin_hub.iter_loaded_plugins():
            print(f"{plugin.name}")
        print()
