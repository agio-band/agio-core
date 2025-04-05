from abc import ABC

from agio.core.plugins.mixins import BasePluginClass
from agio.core.plugins.plugin_base import APlugin
import click


class AbstractCommand(ABC):
    plugin_type = 'command'
    command_name = None
    arguments = []
    add_context = False
    context_settings = None
    help = None

    def __init__(self, parent_group=None):
        self._init_click(parent_group)

    def _init_click(self, parent_group=None):
        if not self.command_name:
            raise ValueError(f"{self.__class__.__name__}: Command name must be defined.")
        self.command = click.Command(
            name=self.command_name,
            context_settings=self.context_settings,
            callback=self.execute,
            help=self.help
        )
        if self.arguments:
            for arg in self.arguments:
                self.command = arg(self.command)
        if parent_group:
            parent_group.add_command(self.command)

    def execute(self, *args, **kwargs):
        raise NotImplementedError


class ACommand(BasePluginClass, AbstractCommand, APlugin):
    __is_subcommand = False

    def __init__(self, package: "APackage", parent_group=None):
        APlugin.__init__(self, package)
        AbstractCommand.__init__(self, parent_group)


class AGroupCommand(BasePluginClass, AbstractCommand, APlugin):
    command_name = None
    commands = []
    invoke_without_command = False
    help = None

    def __init__(self, package: "APackage", parent_group=None):
        APlugin.__init__(self, package)
        AbstractCommand.__init__(self, parent_group)

    def _init_click(self, parent_group=None):
        if not self.command_name:
            raise ValueError(f"{self.__class__.__name__}: Command name must be defined.")
        if not self.commands:
            raise ValueError(f"{self.__class__.__name__}: Commands must be defined.")
        self.command = click.Group(
            name=self.command_name,
            help=self.help,
            invoke_without_command=self.invoke_without_command,
        )
        for cmd_cls in self.commands:
            cmd = cmd_cls(package=self.package)
            self.command.add_command(cmd.command)
