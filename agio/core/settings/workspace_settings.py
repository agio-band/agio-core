from typing import Any

from agio.core.settings.package_settings import APackageSettings
from agio.core.workspace.workspace import AWorkspace
from agio.core.main import package_hub


class AWorkspaceSettings:
    def __init__(self, settings_data: dict[str, Any], **kwargs):
        package_names = set()
        for key in settings_data.keys():
            if key.count('.') != 1:
                raise ValueError(f'Invalid key: {key}. Correct format is "package.parameter"')
            package_names.add(key.rsplit('.')[0])

        self._package_settings = {}
        all_packages = package_hub.get_packages()
        for package_name in package_names:
            if package_name not in all_packages:
                raise ValueError(f'Package {package_name} not found')
            package_settings_cls = all_packages[package_name].get_workspace_settings_class()
            if package_settings_cls:
                package_settings = {k.split('.')[-1]: v for k, v in settings_data.items() if k.startswith(package_name)}
                self._package_settings[package_name] = package_settings_cls(
                    **package_settings,
                    _get_other_parm_func=self.get_parameter,
                )

    def iter_package_settings(self):
        yield from self._package_settings.values()

    def get(self, param_name: str) -> Any:
        if param_name.count('.') != 1:
            raise NameError(f"Invalid parameter name: {param_name}")
        package_name, param_name = param_name.split(":")
        package_settings: APackageSettings = self._package_settings.get(package_name)
        if not package_settings:
            raise KeyError(f"Package {package_name} not found in workspace settings")
        return package_settings.get(param_name)

    def get_parameter(self, param_name: str) -> Any:
        if param_name.count('.') != 1:
            raise NameError(f"Invalid parameter name: {param_name}")
        package_name, param_name = param_name.split(":")
        package_settings: APackageSettings = self._package_settings.get(package_name)
        if not package_settings:
            raise KeyError(f"Package {package_name} not found in workspace settings")
        return package_settings.get_parameter(param_name)
