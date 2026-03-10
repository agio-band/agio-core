from __future__ import annotations

import os
from functools import cached_property
from pathlib import Path

import click
from pydantic import BaseModel

from agio.core.events import emit
from agio.tools import launching, env_names
from agio.tools.process_utils import start_process
from agio.apps.base_classes import base_app_launcher_plugin as bp
from agio.apps.exceptions import ApplicationError, ApplicationNotFoundError


class AApplicationLauncher:
    """Wrapper class for any app plugin"""
    default_python_version = None

    def __init__(
            self,
            app_plugin: bp.AppLauncherPlugin,
            version: str,
            config: dict[str, str],
        ) -> None:
        self._app_plugin = app_plugin
        self._version = version
        if isinstance(config, BaseModel):
            config = config.model_dump()
        self._config = config
        self.ctx = self._create_launch_context()

    def __str__(self):
        return f'{self.label} v{self._version} [{self._app_plugin.app_mode}]'

    def __repr__(self):
        return f"<ApplicationLauncher({self.name!r} v{self._version!r}, [{self._app_plugin.app_mode!r}])"

    def _create_launch_context(self) -> launching.LaunchContext:
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
        return self._app_plugin.app_group

    @property
    def mode(self):
        return self._app_plugin.app_mode

    @property
    def mode_label(self):
        return self._app_plugin.app_mode_label

    @property
    def icon(self):
        return self._app_plugin.icon

    @cached_property
    def config(self) -> dict[str, str]:
        return self._config.copy()

    def get_executable(self):
        return self._app_plugin.get_executable(self)

    def get_python_version(self) -> str|None:
        from agio.apps import app_hub

        # from config
        version = self.config.get('python_version')
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
        config_envs = self._config.get('env') or {}
        plugin_envs = self._app_plugin.get_launch_envs(self, config_envs)
        if not isinstance(self.groups, (list, tuple, set)):
            groups = {self.groups}
        else:
            groups = self.groups
        app_envs = dict(
            **config_envs,
            **(plugin_envs or {}),
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
        default_args = self.config.get('arguments') or []
        return self._app_plugin.get_launch_args(self, default_args)

    def get_install_dir(self):
        path = self.config.get('install_dir')
        if not path:
            raise ApplicationError(f'{self.name} v{self.version} config must define an install dir')
        return path

    def before_start(self):
        pass

    def silent_echo(self):
        return bool(os.getenv('AGIO_SILENT_APP_STARTUP'))

    def start(self, **kwargs):
        """
        PID equal None is app is started as detached
        """
        if not self.silent_echo():
            ### DEBUG INFO ###########################################################
            # click.secho("Not Implemented", fg='red')
            click.secho('=== Start App: ===================', fg='yellow')
            print('Name:', end=' ')
            click.secho(str(self), fg='green')
            print('CMD:', end=' ')
            click.secho(' '.join(self.ctx.command), fg='green')

            envs = self.get_default_launch_envs()
            if envs:
                for k, v in sorted(envs.items()):
                    print(f"{k}={v}")
            click.secho('=========================================', fg='yellow')

            ##########################################################################

        emit('agio_apps.application.before_start', payload={'app': self})
        self._app_plugin.on_before_startup(self)
        kwargs['new_console'] = kwargs.get('new_console', False)
        kwargs['detached'] = kwargs.get('detached', False)
        kwargs['replace'] = not kwargs['detached']
        start_process(self.ctx.command, env=self.ctx.envs, **kwargs)
        self._app_plugin.on_after_startup(self)
