import click

from agio.core.plugins.base.command_base import ACommandPlugin, ASubCommand
from agio.core.plugins.base.main_app_base import AMainAppPlugin
from agio.core.plugins.plugin_base import APlugin


class StartAppCommand(ACommandPlugin):
    name = "startapp_command"
    command_name = 'startapp'
    arguments = [
        click.argument('app_name'),
    ]

    def execute(self, app_name: str, *args, **kwargs):
        from agio.core.main import plugin_hub
        for plugin in plugin_hub.iter_plugins('main_app'):
            if plugin.name == app_name:
                self.execute_app(plugin, *args, **kwargs)
                break
        else:
            raise Exception(f'App "{app_name}" not found')

    def execute_app(self, app_plugin: AMainAppPlugin, *args, **kwargs):
        try:
            app_plugin.start()
        except KeyboardInterrupt:
            app_plugin.stop()

