import os

import click

from agio.core.plugins import plugin_hub
from agio.core.workspaces.workspace import AWorkspaceManager, DefaultWorkspaceError
from agio.tools import launching, env_names


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
             cls=CustomGroup,
             invoke_without_command=True)
@click.option(
    "-d", "--debug", is_flag=True, default=False,
    envvar='AGIO_DEBUG',
    help="Enable DEBUG mode")
@click.option(
    "-w", "--workspace",
    envvar='AGIO_WORKSPACE',
    help='Execute in workspace (Workspace ID, Revision ID, Settings ID, Project ID)',
    required=False
)
@click.option(
    "-a", "--app",
    envvar='AGIO_APP',
    help='Context application key "name/version". "python" mode is required.',
    required=False
)
@click.pass_context
def agio_group(ctx, workspace, debug, app, **kwargs):
    """
    default env -> workspace env -> app env
    """
    if getattr(ctx, 'obj', None) or app:
        obj = getattr(ctx, 'obj') or {}
        cmd_name = obj.get('cmd_name')
        cmd_args = obj.get('cmd_args', [])
        is_unknown = obj.get('is_unknown_command', False)

        if workspace:
            if not AWorkspaceManager.is_current(workspace):
                ws = AWorkspaceManager.create_from_id(workspace)
                full_command = ['-a', app, cmd_name, *cmd_args] if app else [cmd_name, *cmd_args]
                # restart in new workspace
                launching.exec_agio_command(full_command, ws, replace=True)
        if app:
            ws = AWorkspaceManager.current()
            if not ws:
                raise DefaultWorkspaceError
            # set application for current workspace
            ws.set_app(app)
            full_command = [cmd_name, *cmd_args]
            # restart in workspace with app executable
            launching.exec_agio_command(full_command, ws, replace=True)
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
        os.environ[env_names.DEBUG] = 'true'


@agio_group.command(help='Test ping command')
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
