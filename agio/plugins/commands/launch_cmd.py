import click

from agio.apps import app_hub, AApplicationLauncher
from agio.core.events import emit
from agio.core.plugins.base_command import ACommandPlugin
from agio.tools import env_names


class LauncherCommand(ACommandPlugin):
    name = 'launch_cmd'
    command_name = "launch"
    arguments = [
        click.option("-n", "--app-name", help="App Name"),
        click.option("-v", "--app-version", help="App Version"),
        click.option("-m", "--app-mode", default='default', help="App Mode"),
        click.option("-a", "--app", help="App Launch Name"),
        click.option("-t", "--task-id", envvar=env_names.TASK_ID),
        click.option("-d", "--detached", is_flag=True, default=False, help="Start detached without console"),
        click.option("-c", "--new-console", is_flag=True, default=False, help="Open app in a new console"),
        click.option("-k", "--keep-console", is_flag=True, default=False,
                     help="Keep the new console open on error (used with --new-console)"),
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
                keep_console: bool = False,
                env: list[str] = None,
                __extra_args__: list = None,
                **kwargs):
        app_name, app_version, app_mode = self.get_app_values(app_name, app_version, app_mode, app)
        new_app: AApplicationLauncher = app_hub.get_app(app_name, app_version, mode=app_mode)
        if not task_id and new_app.plugin.task_id_required:
            raise click.BadOptionUsage('task-id', 'task-id is required')
        if __extra_args__:
            kwargs['cmd_args'] = __extra_args__
        kwargs['cmd_envs'] = {}
        if task_id:
            kwargs['cmd_envs'] = {env_names.TASK_ID: task_id}
        if env is not None:
            kwargs['cmd_envs'].update(self.parse_envs(env))
        # start mode - exactly one of three
        if new_console:
            # dedicated console: lives while the app runs and shows its output;
            # with keep_console it stays open on error
            kwargs.update(dict(
                new_console=True,
                keep_console=keep_console,
                non_blocking=True,
                detached=False,
                replace=False,
            ))
        elif detached:
            # background process without any console
            kwargs.update(dict(
                detached=True,
                new_console=False,
                non_blocking=False,
                replace=False,
            ))
        else:
            # replace the current process:
            # everything runs in the current console with the same pid
            kwargs.update(dict(
                replace=True,
                new_console=False,
                detached=False,
                non_blocking=False,
            ))
        kwargs['exit_on_done'] = False
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
            # allow the combined "name/version/mode" form for --app-name as well
            if '/' in app_name and not app_version and app_mode == 'default':
                values = app_name.split('/')
                values += ([None]*(3-len(values)))
                app_name, app_version, app_mode = values
            return app_name, app_version, app_mode
        else:
            values = app.split('/')
            values += ([None]*(3-len(values)))
            return values



