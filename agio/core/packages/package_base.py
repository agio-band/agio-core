import os
from pathlib import Path
from typing import Generator, Type, Any

from agio.core.plugins.plugin_base import APlugin


class APackageBase:
    manifest_file_name = '__agio__.yml'
    def __init__(self, package_root: str):
        self.manifest_file = Path(package_root, self.manifest_file_name)
        self._manifest_data = self._check_manifest_data(self._load_manifest(self.manifest_file), self.manifest_file)

    def __str__(self) -> str:
        return f"{self.label} v{self.version}"

    def __repr__(self) -> str:
        return f"APackage({self.name} v{self.version})"

    @property
    def root(self) -> Path:
        return self.manifest_file.parent

    @property
    def name(self) -> str:
        return self._manifest_data['name']

    @property
    def label(self) -> str:
        return self._manifest_data['label']

    @property
    def version(self) -> str:
        return self._manifest_data['version']

    @property
    def icon_name(self) -> str | None:
        return self._manifest_data.get('icon', None)

    @property
    def icon_path(self) -> str:
        return 'not-implement'

    @property
    def info(self) -> dict:
        from agio.core.init_core import app_context

        return {
            'name': self.name,
            'label': self.label,
            'icon': self.icon_name,
            'version': self.version,
            'app_name': app_context.app_name,
            'app_group': app_context.app_group,
            'manifest_file': self.manifest_file.as_posix(),
            'root': self.root.as_posix(),
        }

    def check_installation(self):
        pass

    def get_resource_path(self):
        return self.root / 'resources'

    def collect_plugins(self):
        plugin_info: dict
        for plugin_info, plugin_class in self.iterate_plugin_classes():
            instance = plugin_class(plugin_info, self)
            yield instance

    def iterate_plugin_classes(self) -> Generator[tuple[dict, Type[APlugin]], None, None]:
        plugin_info: dict
        for plugin_info in self.iter_plugin_descriptions():
            for plugin in APlugin.load_from_manifest_data(plugin_info, self.manifest_file.as_posix()):
                if plugin:
                    yield plugin_info, plugin

    def iter_plugin_descriptions(self) -> Generator[list[dict[str, Any]], None, None]:
        plugins = self._manifest_data.get('plugins', [])
        if not plugins:
            return
        if not isinstance(plugins, list):
            raise ValueError(f"Plugins must be a list [{self.manifest_file}]")
        yield from plugins

    @classmethod
    def is_package_root(cls, path: str) -> bool:
        return os.path.exists(path + "/__agio__.yml")

    @classmethod
    def _load_manifest(cls, manifest_file: str|Path) -> dict:
        import yaml
        with open(manifest_file, 'r') as f:
            return yaml.safe_load(f)

    @classmethod
    def _check_manifest_data(cls, manifest_data: dict, manifest_file_path: str|Path) -> dict:
        # manifest is not empty
        if not manifest_data:
            raise ValueError(f"Manifest file is empty [{manifest_file_path}]")
        # manifest data is dict
        if not isinstance(manifest_data, dict):
            raise ValueError(f"Manifest file is not a dictionary [{manifest_file_path}]")
        # required fields exists and not empty
        required_fields = ('name', 'label', 'version')
        for field in required_fields:
            if field not in manifest_data:
                raise ValueError(f"Manifest file is missing required field: {field} [{manifest_file_path}]")
            if not manifest_data[field]:
                raise ValueError(f"Manifest field {field} is empty [{manifest_file_path}]")
        return manifest_data


class APackage(APackageBase):
    pass
