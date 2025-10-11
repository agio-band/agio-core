from collections import defaultdict

import click

from agio.core.pkg import AWorkspaceManager
from agio.core.plugins.base_command import ACommandPlugin, ASubCommand
from agio.core.pkg.workspace import AWorkspace
from agio.core.utils.file_utils import get_folder_size
from agio.core.utils.text_utils import pretty_size


class InstallWorkspaceCommand(ASubCommand):
    command_name = 'install'
    arguments = [
        click.argument('workspace_id'),
        click.option('--clean', '-c', is_flag=True, default=False, help='Delete all before install workspace'),
        click.option('--no-cache', '-n', is_flag=True, default=False, help="Don't use package cache"),
    ]
    help = 'Install workspace by ID'

    def execute(self, workspace_id: str, clean: bool = False, no_cache=False):
        AWorkspace(workspace_id).get_manager().install(clean=clean, no_cache=no_cache)


class UninstallWorkspaceCommand(ASubCommand):
    command_name = 'uninstall'
    arguments = [
        click.argument('workspace_id'),
    ]
    help = 'Uninstall workspace'

    def execute(self, workspace_id: str):
        print('Uninstall Workspace', workspace_id)
        AWorkspace(workspace_id).get_manager().remove()


class ListWorkspaceCommand(ASubCommand):
    command_name = 'ls'
    help = 'List workspaces'

    def execute(self):
        ws_list = defaultdict(list)
        width = 0
        if not AWorkspaceManager.workspaces_root.exists():
            print(f'No installed workspaces yet. \nInstall root is not exists: {AWorkspaceManager.workspaces_root.as_posix()}')
            return
        for ws in AWorkspaceManager.workspaces_root.iterdir():
            for rev in ws.iterdir():
                ws_list[ws.name].append({'rev': rev.name, 'size': get_folder_size(rev)})
                width = max(width, len(rev.name))
        if not ws_list:
            print('No workspaces found')
            return
        print('⎯' * int(width * 1.5))
        print('ROOT:', AWorkspaceManager.workspaces_root)
        print('⎯'*int(width*1.5))
        for w, rev_list in ws_list.items():
            if rev_list:
                print('{:<{width}}    {size}'.format(w, width=width, size=pretty_size(sum([r['size'] for r in rev_list]))))
                for rev in rev_list:
                    print('  {:<{width}}  {size}'.format(rev['rev'], width=width, size=pretty_size(rev['size'])))
        print('⎯' * int(width * 1.5))
        total_size = sum(sum([r['size'] for r in rev_list]) for rev_list in ws_list.values())
        print('Total size', pretty_size(total_size))
        print('⎯' * int(width * 1.5))


class ShowWorkspaceDetailCommand(ASubCommand):
    command_name = 'show'
    arguments = [
        click.argument('workspace_id'),
    ]
    help = 'Show workspace details'

    def execute(self, workspace_id: str):
        print('Workspace ID:', workspace_id)
        ws_man = AWorkspaceManager.create_from_id(workspace_id)
        print('Installed Packages:')
        for pkg in ws_man.get_package_list():   # get from meta file
            print(pkg.get_package_name(), pkg.get_version())
        # TODO installation date
        # TODO last used time
        # TODO total size


class UpdateWorkspaceCommand(ASubCommand):
    command_name = 'update'
    arguments = [
        click.argument('workspace_id', envvar='AGIO_WORKSPACE_ID'),
    ]
    help = 'Show workspace details'

    def execute(self, workspace_id: str):
        # TODO replace with reinstall()
        print('Update workspace:', workspace_id)
        AWorkspaceManager.create_from_id(workspace_id).install_or_update_if_needed()


class WorkspaceCommand(ACommandPlugin):
    name = 'workspace_cmd'
    command_name = "ws"
    subcommands = [InstallWorkspaceCommand,
                UninstallWorkspaceCommand,
                ListWorkspaceCommand,
                UpdateWorkspaceCommand,
                ShowWorkspaceDetailCommand,
               ]
    help = 'Manage workspaces'

