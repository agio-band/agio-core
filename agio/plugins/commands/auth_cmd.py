from agio.core.plugins.base.base_plugin_command import ACommandPlugin


class LoginCommand(ACommandPlugin):
    command_name = 'login'

    def execute(self, *args, **kwargs):
        raise NotImplementedError()


class LogoutCommand(ACommandPlugin):
    command_name = 'logout'

    def execute(self, *args, **kwargs):
        raise NotImplementedError()

