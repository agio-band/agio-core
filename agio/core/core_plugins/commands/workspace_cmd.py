import click
from agio.core.plugins.plugin_cmd_base import ACommand


class WorkspaceCommand(ACommand):
    command_name = 'ws'
    arguments = [
        click.argument('action'),
        click.option("-id", "--workspace_id", help='Workspace ID'),
    ]

    def execute(self, action: str, workspace_id: str):
        match action:
            case 'install':
                self.install(workspace_id)
            case 'uninstall':
                self.uninstall(workspace_id)
            case 'list':
                self.list()
            case 'show':
                self.show(workspace_id)
            case _:
                print(f"Unknown action: {action}")

    def install(self, workspace_id: str):
        if not workspace_id:
            raise Exception('ID is required')
        print('Install Workspace', workspace_id)

    def uninstall(self, workspace_id: str):
        if not workspace_id:
            raise Exception('ID is required')
        print('Uninstall Workspace', workspace_id)

    def list(self):
        print('List Workspaces')

    def show(self, workspace_id: str):
        if not workspace_id:
            raise Exception('ID is required')
        print('Show workspace details:', workspace_id)

