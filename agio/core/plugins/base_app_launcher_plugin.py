from __future__ import annotations

from functools import cached_property
from pathlib import Path

from agio.core.plugins.base_plugin import APlugin
from agio.apps import launcher as bapp
from agio.apps.exceptions import ApplicationError
from agio.tools.launching import LaunchContext


class ApplicationPlugin(APlugin):
    __is_base_plugin__ = True

    plugin_type = 'application'
    required_attrs = {'app_name', 'app_mode', 'app_groups'}

    app_name: str = None
    app_label: str = None
    app_mode: str = None
    app_groups: set[str] = None
    _plugin_type_groups: set[str] = None
    app_icon: str = None
    app_executable_file: str = None
    version_required: bool = False

    def __str__(self):
        return f"{self.app_name}/{self.app_mode}"

    def __repr__(self):
        return f"<{self.__class__.__name__} {self}>"

    @property
    def name(self):
        return self.app_name

    @cached_property
    def label(self):
        return self.app_label or self.app_name.title().replace('_', ' ')

    @cached_property
    def groups(self):
        groups = set()
        if self._plugin_type_groups:
            groups.update(set(self._plugin_type_groups))
        if self.app_groups:
            groups.update(set(self.app_groups))
        return groups

    @property
    def icon(self):
        return self.app_icon

    def get_launch_args(self, settings_args: list = None) -> tuple|list|None:
        """
        Extend or modify args
        """
        return settings_args

    def get_launch_envs(self, envs: dict = None):
        """Create custom envs"""
        return {}

    def get_user_prefs_dir(self):
        pass

    def get_work_dir(self):
        pass

    def executable_name(self) -> str:
        if not self.app_executable_file:
            raise ApplicationError('Executable file not provided')
        return self.app_executable_file

    def on_before_startup(self, context: LaunchContext) -> None:
        pass

    def on_after_startup(self) -> None:
        # TODO call from app hub
        pass

    def on_after_shutdown(self) -> None:
        # TODO call from app hub
        pass


class DccApplicationPlugin(ApplicationPlugin):
    local_settings_required = True
    _plugin_type_groups = {'dcc'}
    required_attrs = {'app_name', 'app_groups', 'app_mode', 'app_executable_file'}

