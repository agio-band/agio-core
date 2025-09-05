import logging
import os
import sys
from collections.abc import Callable
from typing import Iterable

import click

from agio.core.utils  import plugin_hub
from agio.core.pkg.workspace import AWorkspaceManager
from agio.core.utils import launch_utils


def extra_context_args():
    """
    Collect context args from plugins
    """
    plugins = list(plugin_hub.APluginHub.instance().get_plugins_by_type('extra_context_args'))
    if plugins:
        def inter_options() -> Iterable[Callable]:
            for plg in plugins:
                args = plg.get_args()
                if not isinstance(args, Iterable):
                    args = [args]
                yield from args

        def decorator(f):
            for opt in inter_options():
                f = opt(f)
            return f
    else:
        def decorator(f):
            return f
    return decorator

# base command
@click.group(name='agio')
@click.option(
    "-d", "--debug", is_flag=True, default=False,
    envvar='AGIO_DEBUG',
    help="Enable DEBUG mode")
@click.option(
    "-w", "--workspace",
    help='Execute in workspace (Workspace ID, Revision ID, Settings ID, Project ID)',
    required=False
)
@extra_context_args()
@click.pass_context
def agio_group(ctx, workspace, debug, **kwargs):
    if not AWorkspaceManager.is_defined():
        ws: AWorkspaceManager|None = create_launch_context(workspace, debug, kwargs)
        if ws:
            # execute in different env if not current ws is defined
            command_args = launch_utils.clear_args(sys.argv)
            launch_utils.start_in_workspace(command_args, ws)
            ctx.exit()
    if debug:
        os.environ['DEBUG'] = 'true'


def create_launch_context(workspace_id: str, debug: bool, extra_kwargs):
    ws: AWorkspaceManager | None = launch_utils.get_launch_context_from_args(workspace_id)
    for plg in plugin_hub.APluginHub.instance().get_plugins_by_type('extra_context_args'):
        # any context plugin can add extra envs and other modifications
        plg.execute(ws, **extra_kwargs)
    return ws


@agio_group.command
def ping():
    click.secho('PONG', fg='green')


def load_plugins():
    """
    Collect command plugins and register in cli
    """
    all_command_plugins = list(plugin_hub.APluginHub.instance().get_plugins_by_type('command'))
    for plugin in all_command_plugins:
        agio_group.add_command(plugin.command)


# init command plugins from all packages
load_plugins()
