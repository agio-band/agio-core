import os
import sys
import click

from agio.core.cli import tools
from agio.core import plugin_hub
from agio.core.workspace import AWorkspace


# base command
@click.group(name='agio')
@click.option(
    "-d", "--debug", is_flag=True, default=False,
    help="Enable DEBUG mode")
@click.option(
    "-n", "--project_name",
    envvar='AGIO_PROJECT_NAME',
    help='Execute in project (NAME)',
    required=False
)
@click.option(
    "-p", "--project_id",
    envvar='AGIO_PROJECT_ID',
    help='Execute in project (ID)',
    required=False
)
@click.option(
    "-w", "--workspace_id",
    envvar='AGIO_WORKSPACE_ID',
    help='Execute in workspace (ID)',
    required=False
)
@click.option(
    "-s", "--workspace_name",
    envvar='AGIO_WORKSPACE_NAME',
    help='Execute in workspace (NAME)',
    required=False
)
@click.option(
    "-r", "--revision_id",
    envvar='AGIO_REVISION_ID',
    help='Execute in revision (ID)',
    required=False
)
@click.pass_context
def agio_group(ctx, project_name, project_id, workspace_id, workspace_name, revision_id, debug):
    if not AWorkspace.current():
        ws: AWorkspace|None = tools.get_workspace_from_args(
            project_name=project_name,
            project_id=project_id,
            workspace_id=workspace_id,
            workspace_name=workspace_name,
            revision_id=revision_id,
        )
        if ws:
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
