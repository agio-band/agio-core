import click
from agio.core.plugins.base.base_plugin_command import ACommand, AGroupCommand
from agio.core.workspace.workspace import AWorkspace


class InstallWorkspaceCommand(ACommand):
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
        # todo: show table of workspaces
        for ws in AWorkspace.workspaces_root.iterdir():
            print(ws.name)


class ShowWorkspaceDetailCommand(ACommand):
    command_name = 'show'
    arguments = [
        click.argument('workspace_id'),
    ]
    help = 'Show workspace details'

    def execute(self, workspace_id: str):
        print('Show workspace details:', workspace_id)


class UpdateWorkspaceDetailCommand(ACommand):
    command_name = 'update'
    arguments = [
        click.argument('workspace_id', envvar='AGIO_WORKSPACE_ID'),
    ]
    help = 'Show workspace details'

    def execute(self, workspace_id: str):
        print('Update workspace details:', workspace_id)
        AWorkspace(workspace_id).update()


class WorkspaceCommandGroup(AGroupCommand):
    command_name = "ws"
    commands = [InstallWorkspaceCommand,
                UninstallWorkspaceCommand,
                ListWorkspaceCommand,
                UpdateWorkspaceDetailCommand,
                ShowWorkspaceDetailCommand,]
    help = 'Manage workspaces'

