from __future__ import annotations

import re
from typing import Generator

from agio.apps.base_classes import base_app_launcher_plugin as bp
from agio.apps.exceptions import ApplicationNotFoundError, AppLocalSettingsNotFoundError, ApplicationError
from agio.apps.launcher import AApplicationLauncher
from agio.core.plugins import plugin_hub
from agio.core.settings import get_local_settings
from agio.tools.singleton import Singleton


class ApplicationHub(metaclass=Singleton):
    """
    TODO
    - process watch and control
    """
    def __init__(self):
        local_settings = get_local_settings()
        self.apps_config = local_settings.get('agio_core.applications', [])

    def get_app(self, name: str, version: str = None, mode: str = 'default') -> AApplicationLauncher:
        plugin = self.find_plugin(name, mode)
        if not plugin:
            raise ApplicationNotFoundError(f"Plugin '{name}/{mode}' not found")
        app_config = None
        try:
            app_config = self.get_app_settings(name, version) or {} # TODO error if empty
        except ApplicationNotFoundError:
            if plugin.local_settings_required:
                raise
        return AApplicationLauncher(plugin, version, app_config)

    @classmethod
    def parse_key(cls, app_key: str, version: str = None, mode: str = None) -> tuple[str, ...]:
        match = re.match(r"([^/]+)/?([^/]+)?/?([^/]+)?", app_key)
        if not match:
            raise ApplicationNotFoundError(f"Invalid app key '{app_key}'")
        app_name, app_version, app_mode = match.groups()
        return app_name, version or app_version, mode or app_mode

    def get_app_settings(self, name: str, version: str) -> dict:
        for app in self.apps_config:
            if app.name == name and app.version == version:
                return app.model_dump()
        raise AppLocalSettingsNotFoundError('Application settings for {} v{} not found'.format(name, version))

    @classmethod
    def find_plugin(cls, name: str, mode: str = 'default') -> bp.AppLauncherPlugin | None:
        for plg in cls.find_app_plugins(name):
            if plg.app_mode == mode:
                return plg
        return None

    @classmethod
    def find_app_plugins(cls, name: str) -> Generator[bp.AppLauncherPlugin, None]:
        hub = plugin_hub.APluginHub.instance()
        for app_plugin in hub.get_plugins_by_type('app_launcher'):
            if app_plugin.app_name == name:
                yield app_plugin
