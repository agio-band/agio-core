from typing import Any

from agio.core.settings.package_settings import APackageSettings
from agio.core.workspace.workspace import AWorkspace
from agio.core.main import package_hub


class ASettingsHub:
    settings_type: str = None

    def __init__(self, settings_data: dict[str, Any], **kwargs):
        if self.settings_type is None:
            raise RuntimeError('Settings type not set')
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
            if self.settings_type == LocalSettingsHub.settings_type:
                package_settings_cls = all_packages[package_name].get_local_settings_class()
            elif self.settings_type == WorkspaceSettingsHub.settings_type:
                package_settings_cls = all_packages[package_name].get_workspace_settings_class()
            else:
                raise ValueError(f'Invalid settings type: {self.settings_type}')
            if package_settings_cls:
                package_settings = {k.split('.')[-1]: v for k, v in settings_data.items() if k.startswith(package_name)}
                self._package_settings[package_name] = package_settings_cls(
                    **package_settings,
                    _package_name=package_name,
                    _get_other_parm_func=self.get_parameter,
                )

    def __str__(self):
        return f"{self.__class__.__name__}:({', '.join(self._package_settings.keys())})"

    def __repr__(self):
        return f"<{self}>"

    def iter_package_settings(self):
        yield from self._package_settings.values()

    def get(self, param_name: str) -> Any:
        if param_name.count('.') != 1:
            raise NameError(f"Invalid parameter name: {param_name}")
        package_name, param_name = param_name.split(".")
        package_settings: APackageSettings = self._package_settings.get(package_name)
        if not package_settings:
            raise KeyError(f"Package {package_name} not found in workspace settings")
        return package_settings.get(param_name)

    def set(self, param_name: str, value: Any):
        if param_name.count('.') != 1:
            raise NameError(f"Invalid parameter name: {param_name}")
        package_name, param_name = param_name.split(".")
        package_settings = self._package_settings.get(package_name)
        if not package_settings:
            raise KeyError(f"Package {package_name} not found in workspace settings")
        return package_settings.set(param_name, value)

    def get_parameter(self, param_name: str) -> Any:
        if param_name.count('.') != 1:
            raise NameError(f"Invalid parameter name: {param_name}")
        package_name, param_name = param_name.split(":")
        package_settings: APackageSettings = self._package_settings.get(package_name)
        if not package_settings:
            raise KeyError(f"Package {package_name} not found in workspace settings")
        return package_settings.get_parameter(param_name)

    def dump(self):
        all_settings = {}
        for name, pkg in self._package_settings.items():
            pkg_settings = {f"{name}.{k}": v for k,v in pkg.__dump_settings__().items()}
            all_settings.update(pkg_settings)
        return all_settings

    def save(self):
        raise NotImplementedError()


class LocalSettingsHub(ASettingsHub):
    settings_type: str = 'local'

    def save(self):
        from agio.core.settings.collector import write_common_settings

        data = self.dump()
        write_common_settings(data)


class WorkspaceSettingsHub(ASettingsHub):
    settings_type: str = 'workspace'

    def save(self):
        """
        Current user must have permissions to save workspace settings
        """
