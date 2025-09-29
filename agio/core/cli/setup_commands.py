import os
import sys

import click

from agio.core.utils  import plugin_hub
from agio.core.pkg.workspace import AWorkspaceManager
from agio.core.utils import launch_utils


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
@click.pass_context
def agio_group(ctx, workspace, debug, **kwargs):
    if not AWorkspaceManager.is_defined():
        # launch new process with some workspace context
        ws: AWorkspaceManager | None = AWorkspaceManager.create_from_id(workspace)
        if ws:
            # execute in different env if not current ws is defined
            # command_args = launch_utils.clear_args(sys.argv)
            pos = sys.argv.index(ctx.invoked_subcommand)
            _, command_args = sys.argv[:pos - 1], sys.argv[pos:]
            launch_utils.start_in_workspace(ws, command_args)
            ctx.exit()
    if debug:
        os.environ['DEBUG'] = 'true'


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
