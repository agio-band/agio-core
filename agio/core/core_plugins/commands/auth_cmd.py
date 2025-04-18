from agio.core.plugins.base.base_plugin_command import ACommand


class LoginCommand(ACommand):
    command_name = 'login'


class LogoutCommand(ACommand):
    command_name = 'logout'

