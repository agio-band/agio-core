import click

from agio.apps import app_hub, AApplicationLauncher
from agio.core.events import emit
from agio.core.plugins.base_command import ACommandPlugin
from agio.tools import env_names


class LauncherCommand(ACommandPlugin):
    name = 'launch_cmd'
    command_name = "launch"
    arguments = [
        click.option("-a", "--app-name", help="App Name"),
        click.option("-v", "--app-version", help="App Version"),
        click.option("-m", "--app-mode", default='default', help="App Mode"),
        click.option("-a", "--app", help="App Launch Name"),
        click.option("-t", "--task-id", envvar=env_names.TASK_ID),
        click.option("-d", "--detached", is_flag=True, default=False, help="Start Detached"),
        click.option("-c", "--new-console", is_flag=True, default=False, help="Open in new console"),
        click.option("-e", "--env", multiple=True, help="Extra environment variables"),
    ]
    allow_extra_args = True

    def execute(self,
                task_id: str,
                app_name: str = None,
                app_version: str = None,
                app_mode: str = None,
                app: str = None,
                detached: bool = False,
                new_console: bool = False,
                env: list[str] = None,
                __extra_args__: list = None,
                **kwargs):
        app_name, app_version, app_mode = self.get_app_values(app_name, app_version, app_mode, app)
        new_app: AApplicationLauncher = app_hub.get_app(app_name, app_version, mode=app_mode)
        if not task_id and new_app.plugin.task_id_required:
            raise click.BadOptionUsage('task-id', 'task-id is required')
        click.secho(f'Start app "{app_name}" v{app_version} [{app_mode}]', fg='green')
        if __extra_args__:
            kwargs['cmd_args'] = __extra_args__
        kwargs['cmd_envs'] = {}
        if task_id:
            kwargs['cmd_envs'] = {env_names.TASK_ID: task_id}
        if env is not None:
            kwargs['cmd_envs'].update(self.parse_envs(env))
        kwargs.update(dict(
            detached = detached,
            replace = not new_console,
            new_console = new_console,
            non_blocking = new_console,
            exit_on_done = False,
        ))
        emit('agio_core.start_app.app_created', payload={'app': new_app, 'kwargs': kwargs})
        pid = new_app.start(**kwargs)
        return pid

    def parse_envs(self, envs: list[str]):
        result = {}
        for env in envs:
            key, value = env.split('=')
            result[key] = value
        return result

    def get_app_values(self, app_name, app_version, app_mode, app):
        if app_name and app:
            raise click.BadOptionUsage('app-name', 'app-name and app is mutually exclusive')
        if app_name:
            return app_name, app_version, app_mode
        else:
            values = app.split('/')
            values += ([None]*(3-len(values)))
            return values



