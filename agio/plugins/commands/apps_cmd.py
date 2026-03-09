from agio.core.plugins.base_command import ACommandPlugin, ASubCommand
import click

from agio_apps.exceptions import ApplicationError
from agio_apps.utils import get_app_list


class ListAppCommand(ASubCommand):
    command_name = "ls"
    arguments = [
        click.option('-a', '--as-args', is_flag=True, help='Show as arguments'),
    ]

    def execute(self, as_args: bool):
        apps = list(get_app_list())

        if not apps:
            click.secho('No app plugins found', fg='red')
        for app in apps:
            if as_args:
                click.echo('--app-name {} --app-version {} --app-mode {}'.format(app.name, app.version, app.mode))
            else:
                try:
                    install_dir = app.get_install_dir()
                except ApplicationError:
                    install_dir = None
                click.echo(f'{app}, install dir: {install_dir or "NOT-SET"}') # TODO make beauty


class AddAppCommand(ASubCommand):
    """
    Add application configuration to local config
    """
    command_name = "add"
    arguments = [
        click.option('-n', '--app-name',  required=True, help='Application name'),
        click.option('-v', '--app-version', required=True, help='Application version'),
        click.option('-i', '--installation-dir', required=True,
                     type=click.Path(exists=True, file_okay=False, dir_okay=True, readable=True),
                     help='Installation directory'),
    ]

    def execute(self, app_name, app_version, installation_dir):
        print('Adding app: "{}" v{}'.format(app_name, app_version))


class DelAppCommand(ASubCommand):
    """
    Add application configuration to local config
    """
    command_name = "del"
    arguments = [
        click.option('-n', '--app-name',  required=True, help='Application name'),
        click.option('-v', '--app-version', required=True, help='Application version'),
    ]

    def execute(self, app_name, app_version, installation_dir):
        print('Delete app: "{}" v{}'.format(app_name, app_version))


class LauncherToolsCommand(ACommandPlugin):
    name = "apps_cmd"
    command_name = 'apps'
    subcommands = [ListAppCommand, AddAppCommand, DelAppCommand]


