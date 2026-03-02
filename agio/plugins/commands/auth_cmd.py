import click

from agio.core.api import client
from agio.core.plugins.base_command import ACommandPlugin, ASubCommand


class LoginCommand(ASubCommand):
    command_name = "login"
    arguments = [
        click.option('-f', '--force', is_flag=True, help='Reset locker and restart login process'),
    ]

    def execute(self, force: bool):
        client.login(force=force)


class LogoutCommand(ASubCommand):
    command_name = "logout"

    def execute(self):
        client.logout()


class AuthCommand(ACommandPlugin):
    name = "auth_cmd"
    command_name = 'auth'
    help = 'Authorization commands'
    subcommands = [LoginCommand, LogoutCommand]

    def execute(self, *args, **kwargs):
        print('Show current user info [TODO]')


