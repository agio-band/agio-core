import click

from agio.core.entities import AWorkspaceRevision
from agio.core.plugins.base_command import ASubCommand, ACommandPlugin


class RevisionInfoCommand(ASubCommand):
    command_name = "info"
    arguments = [
        click.argument("revision-id"),
    ]

    def execute(self, revision_id: str, **kwargs):
        rev = AWorkspaceRevision(revision_id)

        def prnt(key, value):
            click.secho(f'{key}:', nl=False, fg='yellow')
            click.secho(value)

        click.secho('Package Common Info:', fg='green')
        prnt('ID', revision_id)
        prnt('Workspace ID ', rev.workspace_id)
        prnt('Workspace Name', rev.get_workspace().name)
        click.secho('Packages:', fg='green')
        for rel in rev.get_package_list():
            click.secho(f'{rel.get_package_name()} v{rel.get_version()} ', nl=False, fg='yellow')
            click.secho(f'({rel.id})')


class RevisionSyncCommand(ASubCommand):
    command_name = "sync"

    def execute(self, *args, **kwargs):
        from agio.core.workspaces import sync_current_workspace
        sync_current_workspace()


class RevisionSyncLocalCommand(ASubCommand):
    command_name = "synclocal"

    def execute(self, *args, **kwargs):
        from agio.core.workspaces import AWorkspaceManager
        manager = AWorkspaceManager.current()
        file = manager.dump_local_settings()
        click.echo(file)


class RevisionCommand(ACommandPlugin):
    name = 'revision_cmd'
    command_name = "revision"
    subcommands = [
        RevisionInfoCommand,
        RevisionSyncCommand,
        RevisionSyncLocalCommand,
    ]
    help = 'Manage workspace revisions'
