from agio.core.plugins.base_plugin import APlugin
from agio.core.settings import BaseField, APackageSettings
from agio.core.settings.settings_hub import ASettingsHub


class SettingsDependencySolverPlugin(APlugin):
    plugin_type = 'settings_dependency_solver'
    __is_base_plugin__ = True

    def execute(self, field: BaseField, package_settings: APackageSettings, settings_hub: ASettingsHub, **kwargs):
        raise NotImplementedError()