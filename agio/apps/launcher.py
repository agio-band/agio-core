from __future__ import annotations

import os
from pathlib import Path
import shlex

import click

from agio.apps.exceptions import ApplicationError, ApplicationNotFoundError
from agio.core.events import emit
from agio.core.plugins import base_app_launcher_plugin as bp
from agio.core.settings import get_local_settings
from agio.package_settings.local_settings import ApplicationSettings
from agio.tools import launching, env_names
from agio.tools.process_utils import start_process


class AApplicationLauncher:
    """Wrapper class for any app plugin"""
    default_python_version = None

    def __init__(
            self,
            app_plugin: bp.ApplicationPlugin,
            version: str|None = None,
        ) -> None:
        self._app_plugin = app_plugin
        self._version = version

        self._settings = self.get_settings()

    def __str__(self):
        return f'{self.label} v{self._version} [{self._app_plugin.app_mode}]'

    def __repr__(self):
        return f"<ApplicationLauncher({self.name!r} v{self._version!r}, [{self._app_plugin.app_mode!r}])"

    def get_settings(self) -> ApplicationSettings|None:
        local_settings = get_local_settings()
        apps_config: list[ApplicationSettings] = local_settings.get('agio_core.applications', [])
        for app_config in apps_config:
            if app_config.name == self.name:
                if app_config.version == self.version:
                    return app_config
        raise ApplicationError(f'Application settings not found: {self}')

    def create_launch_context(self) -> launching.LaunchContext:
        executable = self.get_executable()
        if not executable:
            raise ApplicationError(f'{self.name} must define a executable')
        if not Path(executable).is_file():
            raise ApplicationError(f'Executable {self.name}/{executable} is not a file or not exists')
        ctx = launching.LaunchContext(
            executable,
            args=self.get_default_launch_args(),
            env=self.get_default_launch_envs(),
        )
        return ctx

    def get_install_dir(self, **kwargs):
        path = Path(self._settings.install_dir)
        if not path.is_dir():
            raise ApplicationError(f'{self.name} v{self.version} settings must provide an install dir')
        return path


    def get_executable(self, **kwargs) -> str:
        path = Path(self.get_install_dir(**kwargs), self._app_plugin.executable_name()).as_posix()
        context = {
            'version': self.version,
            # add custom variables
        }
        return path.format(**context)

    def get_default_workdir(self, **kwargs) -> str:
        """
        Modify workdir for current mode
        """
        path = (self._settings.workdir
                or self._app_plugin.get_work_dir()
                or self.get_install_dir(**kwargs)
                )
        # render variables
        return path

    @property
    def label(self):
        return self._app_plugin.get_label()

    @property
    def name(self):
        return self._app_plugin.app_name

    @property
    def version(self):
        return self._version

    @property
    def groups(self):
        return self._app_plugin.app_groups

    @property
    def mode(self):
        return self._app_plugin.app_mode

    @property
    def icon(self):
        return self._app_plugin.icon

    def get_python_version(self) -> str|None:
        from agio.apps import app_hub

        # from config
        version = self._settings.python_version
        if version:
            return version
        try:
            py_app = app_hub.get_app(self.name, self.version, mode='python')
            cmd = [py_app.get_executable(), '-V']
            version = start_process(cmd, get_output=True, new_console=False).split()[-1]
            return version
        except ApplicationNotFoundError:
            return self.default_python_version

    def get_default_launch_envs(self):
        config_envs = self._settings.extra_envs or {}
        plugin_envs = self._app_plugin.get_launch_envs()
        if not isinstance(self.groups, (list, tuple, set)):
            groups = {self.groups}
        else:
            groups = self.groups
        app_envs = dict(
            **config_envs,
            **plugin_envs,
            **{
                env_names.APP_NAME: self.name,
                env_names.APP_GROUPS: ','.join(groups),
                env_names.APP_VERSION:self.version,
                env_names.APP_MODE: self.mode,
                env_names.APP_EXECUTABLE:self.get_executable(),
            }
        )
        return app_envs

    def get_default_launch_args(self):
        default_args = self._settings.extra_args
        if isinstance(default_args, str):
            default_args = shlex.split(default_args)
        return self._app_plugin.get_launch_args(default_args)

    def silent_echo(self):
        return bool(os.getenv('AGIO_SILENT_APP_STARTUP'))

    def start(self, cmd_args: list[str] = None, cmd_envs: dict = None, **kwargs):
        """
        PID equal None is app is started as detached
        """
        context = self.create_launch_context()
        if cmd_args:
            context.add_args(*cmd_args)
        if cmd_envs:
            context.append_envs(**cmd_envs)

        ### DEBUG INFO ###########################################################
        if not self.silent_echo():
            click.secho('=== Start App: ==========================', fg='yellow')
            print('Name:', end=' ')
            click.secho(str(self), fg='green')
            print('CMD:', end=' ')
            click.secho(' '.join(context.command), fg='green')
            envs = self.get_default_launch_envs()
            if cmd_envs:
                envs.update(**cmd_envs)
            for k, v in sorted(envs.items()):
                print(f"{k}={v}")
            click.secho('=========================================', fg='yellow')
        ##########################################################################

        emit('agio_core.application.before_start', payload={'app': self, 'context': context})
        self._app_plugin.on_before_startup(context)
        kwargs.setdefault('new_console', False)
        kwargs.setdefault('detached', False)
        kwargs['replace'] = not kwargs['detached']
        start_process(context.command, env=context.envs, **kwargs)

