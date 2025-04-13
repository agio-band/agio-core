import click
from agio.core.plugins.base.base_plugin_command import ACommand, AGroupCommand
from agio.core.workspace.workspace import AWorkspace


class InstallWorkspaceCommand(ACommand):
    command_name = 'install'
    arguments = [
        click.argument('workspace_id'),
        click.option('--force', '-f', is_flag=True, default=False, help='Force install workspace'),
    ]
    help = 'Install workspace by ID'

    def execute(self, workspace_id: str, force: bool = False):
        print('Install Workspace', workspace_id)
        AWorkspace(workspace_id).install(force=force)



class UninstallWorkspaceCommand(ACommand):
    command_name = 'uninstall'
    arguments = [
        click.argument('workspace_id'),
    ]
    help = 'Uninstall workspace'

    def execute(self, workspace_id: str):
        print('Uninstall Workspace', workspace_id)
        AWorkspace(workspace_id).remove()


class ListWorkspaceCommand(ACommand):
    command_name = 'ls'
    help = 'List workspaces'

    def execute(self):
        print('List Workspaces')


class ShowWorkspaceDetailCommand(ACommand):
    command_name = 'show'
    arguments = [
        click.argument('workspace_id'),
    ]
    help = 'Show workspace details'

    def execute(self, workspace_id: str):
        print('Show workspace details:', workspace_id)


class WorkspaceCommandGroup(AGroupCommand):
    command_name = "ws"
    commands = [InstallWorkspaceCommand, UninstallWorkspaceCommand, ListWorkspaceCommand, ShowWorkspaceDetailCommand]
    help = 'Manage workspaces'

