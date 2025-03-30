from abc import ABC

from agio.core.plugins.mixins import BasePluginClass
from agio.core.plugins.plugin_base import APlugin
import click


class AbstractCommand(ABC):
    plugin_type = 'command'
    command_name = None
    arguments = []
    subcommands = []
    add_context = False
    context_settings = None
    invoke_without_command = False

    def __init__(self, parent_group=None):
        if not self.command_name:
            raise ValueError(f"{self.__class__.__name__}: Command name must be defined.")

        if self.subcommands:
            self.command = click.Group(
                name=self.command_name,
                invoke_without_command=self.invoke_without_command
            )
            for subcmd_cls in self.subcommands:
                subcmd = subcmd_cls(parent_group=self.command)
                self.command.add_command(subcmd.command)
        else:
            @click.command(name=self.command_name, context_settings=self.context_settings)
            def command(**kwargs):
                self.execute(**kwargs)

            for arg in self.arguments:
                command = arg(command)

            self.command = command

        if parent_group:
            parent_group.add_command(self.command)

    def execute(self, *args, **kwargs):
        raise NotImplementedError


class ACommand(BasePluginClass, AbstractCommand, APlugin):
    __is_subcommand = False

    def __init__(self, manifest_data: dict, package: "APackage", parent_group=None):
        APlugin.__init__(self, manifest_data, package)
        AbstractCommand.__init__(self, parent_group)


class SubCommand(BasePluginClass, AbstractCommand):
    __is_subcommand = True
