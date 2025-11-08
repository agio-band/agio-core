import inspect
import json
import logging
import os
from abc import ABC
import click

from agio.core.entities import APackage
from agio.core.events import emit
from agio.core.plugins.mixins import BasePluginClass
from agio.core.plugins.base_plugin import APlugin
from agio.tools import context, env_names
from agio.tools import args_helper
from agio.tools.process_utils import restart_with_env, pipe_is_allowed, write_to_pipe

logger = logging.getLogger(__name__)


class AbstractCommandPlugin(ABC):
    plugin_type = 'command'
    command_name = None
    arguments = []
    add_context = False
    context_settings = None
    subcommands = []
    help = None
    # if True command must accept **kwargs or __extra_args__ argument
    allow_extra_args = False
    # allow "execute()" method for command group if subcommand is not set
    allow_empty_root_command = False
    # execute root command before sub command
    execute_root_command_before_subcommand = False
    # allow to write output to custom pipe
    allow_write_output_to_custom_pipe = bool(os.getenv(env_names.ALLOW_COMMAND_OUTPUT_TO_CUSTOM_PIPE))

    def __init__(self, parent_group=None):
        self._init_click(parent_group)
        self.context = None

    def get_context_settings(self):
        ctx = (self.context_settings or {}).copy()
        if self.allow_extra_args:
            ctx['ignore_unknown_options'] = True
        return ctx or None

    def on_before_execute(self, kwargs):
        emit('core.command.before_execute',{
            'command_name': self.command_name,
            'kwargs': kwargs,
            'context': self.context,
        })

    def on_executed(self, result, kwargs):
        emit('core.command.executed', {
            'command_name': self.command_name,
            'result': result,
            'context': self.context,
            'kwargs': kwargs,
        })
        if self.allow_write_output_to_custom_pipe and pipe_is_allowed():
            try:
                write_to_pipe(json.dumps(result).encode('utf-8'))
            except json.decoder.JSONDecodeError:
                write_to_pipe(str(result).encode('utf-8'))

    def _init_click(self, parent_group=None):
        if not self.command_name:
            raise ValueError(f"{self.__class__.__name__}: Command name must be defined. Class {self.__class__.__name__}")

        @click.pass_context
        def _callback(ctx, **kwargs):
            self.context = ctx
            self.on_before_execute(kwargs)
            if self.subcommands and self.allow_empty_root_command:
                if not self.execute_root_command_before_subcommand and self.context.invoked_subcommand:
                    return
                if self.context.obj and self.context.obj.get('cmd_args'):
                    return
            result = self.execute(**kwargs) # TODO catch Ctrl+C to forced exit
            self.on_executed(result, kwargs)
            return result

        if self.allow_extra_args:
            _callback = click.argument("__extra_args__", nargs=-1, type=click.UNPROCESSED)(_callback)

        for decorator in reversed(self.arguments):
            _callback = decorator(_callback)
        if self.subcommands:
            self.command = click.group(
                name=self.command_name,
                context_settings=self.get_context_settings(),
                help=self.help,
                invoke_without_command=self.allow_empty_root_command,
            )(_callback)
            for subcmd in self.subcommands:
                if inspect.isclass(subcmd):
                    subcmd = subcmd()
                if not isinstance(subcmd, ASubCommand):
                    raise TypeError(f"Subcommand {subcmd} must be an instance of ASubCommand")
                self.command.add_command(subcmd.command)
        else:
            self.command = click.command(
                name=self.command_name,
                context_settings=self.get_context_settings(),
                help=self.help
            )(_callback)
        if parent_group:
            parent_group.add_command(self.command)

    def execute(self, **kwargs):
        pass


class ACommandPlugin(BasePluginClass, AbstractCommandPlugin, APlugin):

    def __init__(self, package: APackage, plugin_info: dict, parent_group=None):
        APlugin.__init__(self, package, plugin_info)
        AbstractCommandPlugin.__init__(self, parent_group)

    def __str__(self):
        return f"{self.__class__.__name__} [{self.package.package_name}]"

    def parse_extra_args(self, kwargs: dict) -> (list, dict):
        if kwargs and "__extra_args__" in kwargs:
            list_extra = kwargs.pop("__extra_args__")
            return args_helper.parse_args_to_dict_and_list(list_extra)
        return (), {}


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
            restart_with_env({env_names.APP_NAME: self.app_name})
            # TODO env_names.APP_VERSION

    def start(self, **kwargs):
        raise NotImplementedError(f'Not implemented in {self.__class__.__name__}')


    def execute(self, **kwargs):
        self.before_start(**kwargs)
        self.start()