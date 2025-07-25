import inspect
import logging
from abc import ABC
import click

from agio.core.entities import APackage
from agio.core.plugins.mixins import BasePluginClass
from agio.core.plugins.base_plugin import APlugin
from agio.core.utils import context
from agio.core.utils.process_utils import restart_with_env

logger = logging.getLogger(__name__)


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

    def before_start(self, **kwargs):
        pass

    def _init_click(self, parent_group=None):
        if not self.command_name:
            raise ValueError(f"{self.__class__.__name__}: Command name must be defined. Class {self.__class__.__name__}")

        @click.pass_context
        def _callback(ctx, **kwargs):
            self.context = ctx
            self.before_start(**kwargs)
            return self.execute(**kwargs)
        for decorator in reversed(self.arguments):
            _callback = decorator(_callback)
        if self.subcommands:
            cmd = click.group(
                name=self.command_name,
                context_settings=self.context_settings,
                help=self.help,
                invoke_without_command=True
            )(_callback)
        else:
            cmd = click.command(
                name=self.command_name,
                context_settings=self.context_settings,
                help=self.help
            )(_callback)

        self.command = cmd

        if self.subcommands:
            for subcmd in self.subcommands:
                if inspect.isclass(subcmd):
                    subcmd = subcmd()
                if not isinstance(subcmd, ASubCommand):
                    raise TypeError(f"Subcommand {subcmd} must be an instance of ASubCommand")
                self.command.add_command(subcmd.command)

        if parent_group:
            parent_group.add_command(self.command)


    def execute(self, **kwargs):
        pass


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


class AStartAppCommand(ACommandPlugin):
    """
    Command for override default standalone application with new app name via restart and replace old process
    """
    app_name = None

    def before_start(self, **kwargs):
        if not self.app_name:
            raise ValueError(f"{self.__class__.__name__}: app_name must be defined.")
        if context.app_name != self.app_name:
            logger.debug(f'Restart as application "{self.app_name}"')
            restart_with_env({'AGIO_APP_NAME': self.app_name})
