from agio.core.api import client
from agio.core.plugins.base_command import ACommandPlugin, ASubCommand


class LoginCommand(ASubCommand):
    command_name = "login"

    def execute(self):
        client.login()


class LogoutCommand(ASubCommand):
    command_name = "logout"

    def execute(self):
        client.logout()


class AuthCommand(ACommandPlugin):
    name = "auth_cmd"
    command_name = 'auth'
    subcommands = [LoginCommand, LogoutCommand]

    def execute(self, *args, **kwargs):
        print('Show current user info [TODO]')


