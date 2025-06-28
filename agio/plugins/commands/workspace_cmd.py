import click
from agio.core.plugins.base.command_base import ACommandPlugin, ASubCommand
from agio.core.workspace.workspace import AWorkspace


class InstallWorkspaceCommand(ASubCommand):
    command_name = 'install'
    arguments = [
        click.argument('workspace_id'),
        click.option('--clean', '-c', is_flag=True, default=False, help='Delete all before install workspace'),
        click.option('--no-cache', '-n', is_flag=True, default=False, help="Don't use package cache"),
    ]
    help = 'Install workspace by ID'

    def execute(self, workspace_id: str, clean: bool = False, no_cache=False):
        print('Install Workspace', workspace_id)
        AWorkspace(workspace_id).install(clean=clean, no_cache=no_cache)



class UninstallWorkspaceCommand(ASubCommand):
    command_name = 'uninstall'
    arguments = [
        click.argument('workspace_id'),
    ]
    help = 'Uninstall workspace'

    def execute(self, workspace_id: str):
        print('Uninstall Workspace', workspace_id)
        AWorkspace(workspace_id).remove()


class ListWorkspaceCommand(ASubCommand):
    command_name = 'ls'
    help = 'List workspaces'

    def execute(self):
        # todo: show table of workspaces
        for ws in AWorkspace.workspaces_root.iterdir():
            print(ws.name)


class ShowWorkspaceDetailCommand(ASubCommand):
    command_name = 'show'
    arguments = [
        click.argument('workspace_id'),
    ]
    help = 'Show workspace details'

    def execute(self, workspace_id: str):
        print('Show workspace details:', workspace_id)


class UpdateWorkspaceCommand(ASubCommand):
    command_name = 'update'
    arguments = [
        click.argument('workspace_id', envvar='AGIO_WORKSPACE_ID'),
    ]
    help = 'Show workspace details'

    def execute(self, workspace_id: str):
        print('Update workspace details:', workspace_id)
        AWorkspace(workspace_id).update()


class WorkspaceCommand(ACommandPlugin):
    name = 'workspace_cmd'
    command_name = "ws"
    commands = [InstallWorkspaceCommand(),
                UninstallWorkspaceCommand(),
                ListWorkspaceCommand(),
                UpdateWorkspaceCommand(),
                ShowWorkspaceDetailCommand(),
               ]
    help = 'Manage workspaces'

    def execute(self, *args, **kwargs):
        pass

