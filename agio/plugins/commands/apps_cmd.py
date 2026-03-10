from agio.apps.launcher import AApplicationLauncher
from agio.core.plugins.base_command import ACommandPlugin, ASubCommand
import click

from agio.apps.exceptions import ApplicationError
from agio.apps import get_registered_apps, get_app_config


class ListAppCommand(ASubCommand):
    command_name = "ls"
    arguments = [
        click.option('-a', '--as-args', is_flag=True, help='Show as arguments'),
    ]

    def execute(self, as_args: bool):
        registered = get_registered_apps()
        if registered:
            click.secho('Registered apps:', fg='yellow')
            for app in registered:
                click.secho(f'  {app.name}')
        else:
            click.secho('No app plugins found', fg='red')
        configs = get_app_config()
        if configs:
            configured = []
            for app_plg in registered:
                conf_list = [x for x in configs if x.name == app_plg.app_name]
                for c in conf_list:
                    app =  AApplicationLauncher(app_plg, c.version, c)
                    try:
                        install_dir = app.get_install_dir()
                    except ApplicationError:
                        install_dir = None
                    configured.append((app, install_dir))
            if configured:
                click.secho('Configs:', fg='yellow')

                for app, install_dir in configured:
                    if as_args:
                        click.echo(f'  --app-name {app.name} --app-version {app.version} --app-mode {app.mode}')
                    else:
                        click.echo(f'  {app.name} v{app.version} [{install_dir or "NOT-SET"}]') # TODO make beauty
            else:
                click.secho('No configured app found', fg='red')



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
        print('TODO: Adding app: "{}" v{}'.format(app_name, app_version))


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
        print('TODO: Delete app: "{}" v{}'.format(app_name, app_version))


class LauncherToolsCommand(ACommandPlugin):
    name = "apps_cmd"
    command_name = 'apps'
    subcommands = [ListAppCommand, AddAppCommand, DelAppCommand]


