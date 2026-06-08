import os

import click

from agio.core.events import emit
from agio.core.plugins.base_command import ACommandPlugin
from agio.apps import app_hub, AApplicationLauncher
from agio.tools import env_names


class LauncherCommand(ACommandPlugin):
    name = 'launch_cmd'
    command_name = "launch"
    arguments = [
        click.option("-a", "--app-name", help="App Name"),
        click.option("-v", "--app-version", help="App Version"),
        click.option("-m", "--app-mode", default='default', help="App Mode"),
        click.option("-t", "--task-id"),
        click.option("-d", "--detached", is_flag=True, default=False, help="Start Detached"),
        click.option("-c", "--new-console", is_flag=True, default=False, help="Open in new console"),
        click.option("-e", "--env", multiple=True, help="Extra environment variables"),
    ]
    allow_extra_args = True

    def execute(self,
                app_name: str,
                app_version: str,
                app_mode: str,
                task_id: str,
                detached: bool = False,
                new_console: bool = False,
                env: list[str] = None,
                __extra_args__: list = None,
                **kwargs):
        if not app_name:
            raise click.BadOptionUsage('app-name', 'app-name not set')
        if not app_version:
            raise click.BadOptionUsage('app_version', 'app-version not set')
        click.secho(f'Start app "{app_name}" v{app_version} [{app_mode}]', fg='green')
        new_app: AApplicationLauncher = app_hub.get_app(app_name, app_version, mode=app_mode)
        if not task_id:
            raise click.BadOptionUsage('task-id', 'Task ID is required')
        if __extra_args__:
            kwargs['cmd_args'] = __extra_args__
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




