import os
import sys
import click

from agio.core.cli.tools import clear_args, start_in_workspace
from agio.core.init_core import plugin_hub


# base command
@click.group(name='agio')
@click.option("-d", "--debug", is_flag=True, default=False, help="Enable debug mode")
@click.option("-ws", "--workspace_id", help='Workspace ID')
@click.pass_context
def agio_group(ctx, workspace_id, debug):
    if workspace_id:
        command_args = clear_args(sys.argv)
        start_in_workspace(command_args, workspace_id)
        ctx.exit()
    if debug:
        click.echo("Debug mode is on")
        os.environ['DEBUG'] = 'true'


def load_plugins():
    """
    Collect command plugins and register in cli
    """
    for plugin in plugin_hub.get_plugins_by_type('command'):
        agio_group.add_command(plugin.command)


# init command plugins from all packages
load_plugins()
