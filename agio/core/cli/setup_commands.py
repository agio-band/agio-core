import os

import click
from agio.core.utils  import plugin_hub
from agio.core.pkg.workspace import AWorkspaceManager
from agio.core.utils import launch_utils


class CustomGroup(click.Group):
    def resolve_command(self, ctx, args):
        try:
            cmd, cmd_name, args = super().resolve_command(ctx, args)
            if not hasattr(ctx, 'obj') or ctx.obj is None:
                ctx.obj = {}
            ctx.obj.update({
                'is_unknown_command': False,
                'cmd_name': cmd_name.name,
                'cmd_args': args,
                'resolved_command': cmd
            })
            return cmd, cmd_name, args

        except click.exceptions.UsageError as e:
            if args and "No such command" in str(e):
                cmd_name = args[0]
                if not hasattr(ctx, 'obj') or ctx.obj is None:
                    ctx.obj = {}
                ctx.obj.update({
                    'is_unknown_command': True,
                    'cmd_name': cmd_name,
                    'cmd_args': args[1:],
                    'resolved_command': None
                })
                @click.command(name=cmd_name)
                def stub_cmd():
                    pass
                return stub_cmd, cmd_name, args[1:]
            raise


# base command
@click.group(name='agio',
             cls=CustomGroup if not AWorkspaceManager.is_defined() else None,
             invoke_without_command=True)
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
    if hasattr(ctx, 'obj') and ctx.obj:
        cmd_name = ctx.obj.get('cmd_name')
        cmd_args = ctx.obj.get('cmd_args', [])
        is_unknown = ctx.obj.get('is_unknown_command', False)
        if not AWorkspaceManager.is_defined() and workspace is not None:
            ws: AWorkspaceManager | None = AWorkspaceManager.create_from_id(workspace)
            if ws:
                # execute in different env if not current ws is defined
                full_command = [cmd_name] + cmd_args
                click.echo(f"CMD: {full_command}")
                click.echo(f"WS: {workspace}")
                launch_utils.exec_agio_command(full_command, ws)
                ctx.exit(0)
            else:
                raise click.exceptions.ClickException('Workspace not found')
        else:
            if is_unknown:
                click.echo(ctx.get_help())
                ctx.exit(1)
            else:
                # exec in default env
                pass

    elif ctx.invoked_subcommand is None:
        # no command
        click.echo(ctx.get_help())
    if debug:
        os.environ['AGIO_DEBUG'] = 'true'


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
