import os
import sys
import click

from agio.core.cli.tools import clear_args, start_in_workspace
from agio.core.init_core import plugin_hub


# base command
@click.group(name='agio')
@click.option("-d", "--debug", is_flag=True, default=False,
              help="Enable DEBUG mode")
@click.option("-ws", "--workspace_id",
              envvar='WORKSPACE_ID',
              help='Execute in workspace (ID)')
@click.pass_context
def agio_group(ctx, workspace_id, debug):
    if workspace_id:
        click.echo(f"Execute in workspace: {workspace_id}")
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
    all_command_plugins = list(plugin_hub.get_plugins_by_type('command'))
    # filter nested commands
    groups = [plg for plg in all_command_plugins if isinstance(plg.command, click.MultiCommand)]
    subcommands = []
    for grp in groups:
        subcommands.extend(grp.commands)
    commands_to_register = [plg for plg in all_command_plugins if plg.__class__ not in subcommands]
    for plugin in commands_to_register:
        agio_group.add_command(plugin.command)


# init command plugins from all packages
load_plugins()
