from agio.apps.launcher import AApplicationLauncher
from agio.core.plugins.base_command import ACommandPlugin, ASubCommand
import click

from agio.apps.exceptions import ApplicationError
from agio.apps import get_registered_app_plugins, get_app_config


class ListAppCommand(ASubCommand):
    command_name = "ls"
    arguments = [
        click.option('-a', '--as-args', is_flag=True, help='Show as arguments'),
    ]

    def execute(self, as_args: bool):
        registered = get_registered_app_plugins()
        configs = get_app_config()
        app_list = []
        for app_plg in registered:
            conf_list = [x for x in configs if x.name == app_plg.app_name]
            if conf_list:
                for c in conf_list:
                    app =  AApplicationLauncher(app_plg, c.version)
                    try:
                        install_dir = app.get_install_dir()
                    except ApplicationError:
                        install_dir = None
                    app_list.append((app, install_dir))
            else:
                app_list.append((AApplicationLauncher(app_plg, None), None))
        if app_list:
            click.secho('Registered applications:', fg='yellow')
            mode_width = max([len(app[0].mode) for app in app_list]) + 1
            for app, install_dir in app_list:
                if as_args:
                    vers_arg = mode_arg = ''
                    if app.version:
                        vers_arg = f'--app-version {app.version} '
                    if app.mode != 'default':
                        mode_arg = f'--app-mode {app.mode} '
                    click.echo(f'  --app-name {app.name} {vers_arg}{mode_arg}')
                else:
                    app_name = click.style(f'{app.name:>10}', fg="blue", bold=True)
                    click.echo(f'  {app_name} | {app.version_str:>10} |{app.mode:>{mode_width}} | {install_dir or ""}')
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


