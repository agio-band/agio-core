import click
from agio.core.plugins.base.command_base_plugin import ACommand, AGroupCommand


class InstallWorkspaceCommand(ACommand):
    command_name = 'install'
    arguments = [
        click.argument('workspace_id'),
    ]
    help = 'Install workspace by ID'

    def execute(self, workspace_id: str):
        print('Install Workspace', workspace_id)


class UninstallWorkspaceCommand(ACommand):
    command_name = 'uninstall'
    arguments = [
        click.argument('workspace_id'),
    ]
    help = 'Uninstall workspace'

    def execute(self, workspace_id: str):
        print('Uninstall Workspace', workspace_id)


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

