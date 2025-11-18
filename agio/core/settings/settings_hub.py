from typing import Any

from agio.core.api.utils import NOTSET
from agio.core.events import emit
from agio.core.settings import package_settings as package_settings_class
from agio.core.settings import collector
from agio.core.workspaces import package_hub


class ASettingsHub:
    settings_type: str = None

    def __init__(self, settings_data: dict[str, Any], **kwargs):

        if self.settings_type is None:
            raise RuntimeError('Settings type not set')
        package_names = set()
        for key in settings_data.keys():
            if key.count('.') != 1:
                raise ValueError(f'Invalid key: "{key}". Correct format is "package.parameter"')
            package_names.add(key.rsplit('.')[0])

        self._package_settings = {}
        all_packages = package_hub.APackageHub.instance().get_packages()
        for package_name in all_packages.keys():
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
        yield from self._package_settings.items()

    def _check_patm_name(self, param_name: str):
        if param_name.count('.') != 1:
            raise NameError(f"Invalid parameter name: {param_name}")

    def get(self, param_name: str, default: Any = NOTSET) -> Any:
        self._check_patm_name(param_name)
        package_name, param_name = param_name.split(".")
        package_settings: package_settings_class.APackageSettings = self._package_settings.get(package_name)
        if not package_settings:
            if default is NOTSET:
                raise KeyError(f"Package {package_name} not found in workspace settings")
            return default
        try:
            return package_settings.get(param_name)
        except ValueError as e:
            if default is not NOTSET:
                return default
            raise e

    def set(self, param_name: str, value: Any):
        self._check_patm_name(param_name)
        package_name, param_name = param_name.split(".")
        package_settings = self._package_settings.get(package_name)
        if not package_settings:
            raise KeyError(f"Package {package_name} not found in workspace settings")
        return package_settings.set(param_name, value)

    def set_default(self, param_name: str) -> None:
        """
        Reset parameter to default value
        """
        self._check_patm_name(param_name)
        parm = self.get_parameter(param_name)
        return parm.set_default()

    def lock(self, param_name: str) -> None:
        self._check_patm_name(param_name)
        parm = self.get_parameter(param_name)
        return parm.lock()

    def unlock(self, param_name: str) -> None:
        self._check_patm_name(param_name)
        parm = self.get_parameter(param_name)
        return parm.unlock()

    def is_locked(self, param_name: str) -> bool:
        self._check_patm_name(param_name)
        parm = self.get_parameter(param_name)
        return parm.is_locked()

    def get_parameter(self, param_name: str) -> Any:
        if param_name.count('.') != 1:
            raise NameError(f"Invalid parameter name: {param_name}")
        package_name, param_name = param_name.split(".")
        package_settings: package_settings_class.APackageSettings = self._package_settings.get(package_name)
        if not package_settings:
            raise KeyError(f"Package {package_name} not found in workspace settings")
        return package_settings.get_parameter(param_name)

    def dump(self, skip_default: bool = True) -> dict:
        all_settings = {}
        for name, pkg in self._package_settings.items():
            pkg_settings = {f"{name}.{k}": v for k,v in pkg.__dump_settings__(skip_default=skip_default).items()}
            all_settings.update(pkg_settings)
        return all_settings

    def save(self):
        raise NotImplementedError()

    def _print_parameters(self):
        """
        Display parameter list for debugging
        """
        max_len = max(map(len, sum([list(k.__schema__().keys()) for k in self._package_settings.values()], [])))
        for name, pkg in self._package_settings.items():
            print('_' * (max_len + 20))
            print(name)
            for param_name, schema in pkg.__schema__().items():
                print(f'  {param_name:>{max_len + 1}}: {schema["field_type"]:>8}: {schema.get("default")}')


class LocalSettingsHub(ASettingsHub):
    settings_type: str = 'local'

    def save(self):
        data = self.dump()
        collector.write_local_settings(data)
        emit('core.settings.local_settings_saved', {'settings': self})


class WorkspaceSettingsHub(ASettingsHub):
    settings_type: str = 'ws'

    # def save(self):
    #     """
    #     Current user must have permissions to save workspace settings
    #     """
