from agio.core.plugins.mixins import BasePluginClass
from agio.core.plugins.plugin_base import APlugin
import click


class ACommand(BasePluginClass, APlugin):
    plugin_type = 'command'
    command_name = None
    arguments = None
    add_context = False
    context_settings = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.command_name:
            raise ValueError("Command name must be defined.")

        @click.command(name=self.command_name, context_settings=self.context_settings)
        def command(**kwargs):
            if self.add_context:
                kwargs['ctx'] = click.get_current_context()
            self.execute(**kwargs)
        if self.arguments:
            for item in reversed(self.arguments):
                command = item(command)
        self.command = command

    def execute(self, *args, **kwargs):
        raise NotImplementedError