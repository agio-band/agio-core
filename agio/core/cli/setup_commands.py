import os

import click
from agio.core.plugins import plugin_hub
from agio.core.workspaces.workspace import AWorkspaceManager
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
             # cls=CustomGroup if not AWorkspaceManager.is_defined() else None,
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
    "-a", "--app-name",
    envvar='AGIO_APP_NAME',
    help='Context application name to launch command',
    required=False
)
@click.option(
    "-v", "--app-version",
    envvar='AGIO_APP_VERSION',
    help='Context application version to launch command',
    required=False
)

@click.pass_context
def agio_group(ctx, workspace, debug, app_name, app_version, **kwargs):
    if bool(app_name) != bool(app_version):
        raise click.UsageError('You must specify both the name and version of the application, or nothing.')
    app_args = []
    if app_name and app_version:
        app_args.extend(['--app-name', app_name, '--app-version', app_version])
    if getattr(ctx, 'obj', None) or app_args:
        obj = getattr(ctx, 'obj') or {}
        cmd_name = obj.get('cmd_name')
        cmd_args = obj.get('cmd_args', [])

        is_unknown = obj.get('is_unknown_command', False)
        if workspace is not None or AWorkspaceManager.is_defined():
            if not AWorkspaceManager.is_defined():
                ws = AWorkspaceManager.create_from_id(workspace)
                full_command = [*app_args, cmd_name, *cmd_args]
                launching.exec_agio_command(full_command, ws, replace=True)
            else:
                current_workspace = AWorkspaceManager.current()
                if workspace:
                    required_workspace = AWorkspaceManager.create_from_id(workspace)
                    if required_workspace.short_key != current_workspace.short_key:
                        full_command = [*app_args, cmd_name, *cmd_args]
                        launching.exec_agio_command(full_command, required_workspace, replace=True)
                if app_name:
                    from agio.apps import app_hub

                    app = app_hub.get_app(app_name, app_version, mode='python')
                    required_workspace = AWorkspaceManager.create_from_id(current_workspace.revision_id)
                    required_workspace.set_app(app)
                    if current_workspace.key != required_workspace.key:
                        full_command = [cmd_name, *cmd_args]
                        launching.exec_agio_command(full_command, required_workspace, replace=False)
                        ctx.exit(0)
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
