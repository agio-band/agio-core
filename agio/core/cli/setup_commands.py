import os
import sys
import click

from agio.core.cli.tools import clear_args, start_in_workspace, ensure_workspace
from agio.core.main import plugin_hub


# base command
@click.group(name='agio')
@click.option("-d", "--debug", is_flag=True, default=False,
              help="Enable DEBUG mode")
@click.option("-w", "--workspace_id",
              envvar='AGIO_WORKSPACE_ID',
              help='Execute in workspace (ID)')
# TODO @click.option("-p", "--project", help='Project ID or name. Autodetect revision ID')
# TODO @click.option("-r", "--workspace_revision_id", help='Workspace revision ID')
@click.pass_context
def agio_group(ctx, workspace_id, debug):
    if workspace_id and not 'AGIO_CURRENT_WORKSPACE' in os.environ:
        command_args = clear_args(sys.argv)
        ensure_workspace(workspace_id)
        start_in_workspace(command_args, workspace_id)
        ctx.exit()
    if debug:
        os.environ['DEBUG'] = 'true'


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
