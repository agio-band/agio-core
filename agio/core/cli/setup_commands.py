import os
import sys
import click

from agio.core.cli import tools
from agio.core import plugin_hub
from agio.core.entities import AWorkspace
from agio.core.pkg.workspace import AWorkspaceManager


# base command
@click.group(name='agio')
@click.option(
    "-d", "--debug", is_flag=True, default=False,
    envvar='AGIO_DEBUG',
    help="Enable DEBUG mode")
@click.option(
    "-p", "--project",
    # envvar='AGIO_PROJECT',
    help='Execute in project (ID or NAME)',
    required=False
)
@click.option(
    "-w", "--workspace",
    # envvar='AGIO_WORKSPACE',
    help='Execute in workspace (Workspace ID or NAME, Revision ID or Settings ID)',
    required=False
)
# @click.option(
#     "-r", "--revision",
#     # envvar='AGIO_WORKSPACE_REVISION',
#     help='Execute in workspace revision (revision ID or settings revision ID)',
#     required=False
# )
@click.pass_context
def agio_group(ctx, project, workspace, debug):
    if not AWorkspaceManager.current():
        ws: AWorkspaceManager|None = tools.get_workspace_from_args(
            project=project,
            workspace=workspace,
        )
        if ws:
            if ws.need_to_reinstall():
                ws.install()
            command_args = tools.clear_args(sys.argv)
            tools.start_in_workspace(ws, command_args)
            ctx.exit()
    if debug:
        os.environ['DEBUG'] = 'true'
    # workspace_id = os.getenv('AGIO_WORKSPACE_ID')
    # revision_id = os.getenv('AGIO_WORKSPACE_REVISION_ID')


@agio_group.command
def ping():
    click.echo('pong')


def load_plugins():
    """
    Collect command plugins and register in cli
    """
    all_command_plugins = list(plugin_hub.get_plugins_by_type('command'))
    for plugin in all_command_plugins:
        agio_group.add_command(plugin.command)


# init command plugins from all packages
load_plugins()
