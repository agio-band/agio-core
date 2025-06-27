import click

from agio.core.plugins.base.command_base import ACommandPlugin, ASubCommand


class LoginCommand(ASubCommand):
    command_name = "login"
    arguments = [
        click.argument("email", type=click.STRING),
        click.argument("password", type=click.STRING),
    ]

    def execute(self, email: str, password: str):
        print(f"Login: {email}@{password}")


class LogoutCommand(ASubCommand):
    command_name = "logout"
    arguments = []

    def execute(self):
        print(f"Logout: ...")


class AuthCommand(ACommandPlugin):
    name = "auth_command"
    command_name = 'auth'
    subcommands = [LoginCommand, LogoutCommand]

    def execute(self, *args, **kwargs):
        print('Show current user info [TODO]')


