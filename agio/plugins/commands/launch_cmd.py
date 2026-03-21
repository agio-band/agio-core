import click

from agio.core.events import emit
from agio.core.plugins.base_command import ACommandPlugin
from agio.apps import app_hub
from agio.tools import env_names


class LauncherCommand(ACommandPlugin):
    name = 'launch_cmd'
    command_name = "launch"
    arguments = [
        # click.option("-n", "--app-name", help="App Name"),
        # click.option("-v", "--app-version", help="App Version"),
        # click.option("-m", "--app-mode", default='default', help="App Mode"),
        click.argument("app"),
        click.option("-t", "--task-id"),
        click.option("-d", "--detached", is_flag=True, default=False, help="Start Detached"),
        click.option("-c", "--new-console", is_flag=True, default=False, help="Open in new console"),
    ]
    allow_extra_args = True

    def execute(self,
                app: str,
                task_id: str,
                __extra_args__: list = None,
                **kwargs):
        app_name, app_version, app_mode = app_hub.parse_key(app)
        if not app_name:
            raise click.BadOptionUsage('app-name', 'app-name not set')
        if not app_version:
            raise click.BadOptionUsage('app_version', 'app-version not set')
        click.secho(f'Start app "{app_name}" v{app_version} [{app_mode}]', fg='green')
        # return self.start_app(app_name, app_version, app_mode, __extra_args__, **kwargs)
        new_app = app_hub.get_app(app_name, app_version, mode=app_mode)
        if not task_id:
            raise click.BadOptionUsage('task-id', 'Task ID is required')
        if __extra_args__:
            kwargs['cmd_args'] = __extra_args__
        kwargs['cmd_envs'] = {env_names.TASK_ID: task_id}
        emit('agio_core.start_app.app_created', payload={'app': new_app})
        kwargs.update(dict(
            detached = False,
            replace = False,
            new_console = False,
            non_blocking = False,
            exit_on_done = False,
        ))
        pid = new_app.start(**kwargs)

    # def start_app(self, app_name, app_version, app_mode, args, **kwargs):
    #     app = app_hub.get_app(app_name, app_version, mode=app_mode)
    #     emit('agio_core.start_app.app_created', payload={'app': app})
    #     # apply default args and envs
    #     if args:
    #         app.ctx.add_args(*args)
    #     # starting...
    #     pid = app.start(**kwargs)
    #     # app started
    #     # !!! this code will not be called if app started with "replace" flag !!!
    #     # move to app process?
    #     emit('agio_core.start_app.after_started', payload={'app': app, 'pid': pid})
    #     return pid



