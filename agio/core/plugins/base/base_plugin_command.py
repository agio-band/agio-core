from abc import ABC
import click

from agio.core.packages.package import APackage
from agio.core.plugins.mixins import BasePluginClass
from agio.core.plugins.plugin_base import APlugin


class AbstractCommandPlugin(ABC):
    plugin_type = 'command'
    command_name = None
    arguments = []
    add_context = False
    context_settings = None
    subcommands = []
    help = None

    def __init__(self, parent_group=None):
        self._init_click(parent_group)
        self.context = None

    def _init_click(self, parent_group=None):
        if not self.command_name:
            raise ValueError(f"{self.__class__.__name__}: Command name must be defined.")

        if self.subcommands:
            @click.group(
                name=self.command_name,
                context_settings=self.context_settings,
                help=self.help,
                invoke_without_command=True  # <-- вот это добавлено
            )
            @click.pass_context
            def group_wrapper(ctx, **kwargs):
                self.context = ctx
                if ctx.invoked_subcommand is None:
                    return self.execute(**kwargs)

            cmd = group_wrapper
        else:
            @click.command(
                name=self.command_name,
                context_settings=self.context_settings,
                help=self.help,
            )
            @click.pass_context
            def command_wrapper(ctx, **kwargs):
                self.context = ctx
                return self.execute(**kwargs)

            cmd = command_wrapper

        for arg in self.arguments:
            cmd = arg(cmd)

        self.command = cmd

        if self.subcommands:
            for subcmd in self.subcommands:
                if not isinstance(subcmd, ASubCommand):
                    raise TypeError(
                        f"Subcommand {subcmd} must be an instance of ASubCommand"
                    )
                self.command.add_command(subcmd.command)

        if parent_group:
            parent_group.add_command(self.command)

    def execute(self, *args, **kwargs):
        raise NotImplementedError(f'Not implemented in {self.__class__.__name__}')


class ACommandPlugin(BasePluginClass, AbstractCommandPlugin, APlugin):

    def __init__(self, package: APackage, plugin_info: dict, parent_group=None):
        APlugin.__init__(self, package, plugin_info)
        AbstractCommandPlugin.__init__(self, parent_group)

    def __str__(self):
        return f"{self.__class__.__name__} [{self.package.name}]"


class ASubCommand(ABC):
    command_name = None
    arguments = []
    help = None

    def __init__(self):
        if not self.command_name:
            raise ValueError(f"{self.__class__.__name__}: command_name must be defined.")
        self.command = click.Command(
            name=self.command_name,
            callback=self.execute,
            help=self.help
        )
        for arg in self.arguments:
            self.command = arg(self.command)

    def execute(self, *args, **kwargs):
        raise NotImplementedError(f'Not implemented in {self.__class__.__name__}')
