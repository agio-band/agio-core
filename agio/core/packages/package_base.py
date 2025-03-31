import os
from pathlib import Path
from typing import Generator, Type, Any, reveal_type, Self

from agio.core.exceptions import PackageError
from agio.core.plugins.plugin_base import APlugin
from agio.core.workspace.request_data import get_package


class APackageBase:
    manifest_file_name = '__agio__.yml'

    def __init__(self, package_name: str, package_version: str, package_root: str|Path = None):
        self._name = package_name
        self._version = package_version
        self._root = Path(package_root) if package_root else None   # used when workspace iterate packages
        self._manifest_data = get_package(package_name, package_version)['manifest']

    def __str__(self) -> str:
        return f"{self.label} v{self.version}"

    def __repr__(self) -> str:
        return f"APackage({self.name} v{self.version})"

    @property
    def name(self) -> str:
        return self._manifest_data['name']

    @property
    def label(self) -> str:
        return self._manifest_data.get('label') or self.name

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
        return {
            'name': self.name,
            'label': self.label,
            'icon': self.icon_name,
            'version': self.version,
            'description': self._manifest_data.get('description', ''),
            'author': self._manifest_data.get('author', ''),
            'author_email': self._manifest_data.get('author_email', ''),
            'license': self._manifest_data.get('license', ''),
            'home_page': self._manifest_data.get('home_page', ''),
        }

    @property
    def root(self):
        return self._root

    @property
    def manifest_file(self):
        if not self.root:
            return
        return self.root / self.manifest_file_name

    @property
    def installation_name(self):
        return f'{self.name}=={self.version}'

    def get_resource_dir(self):
        return self._manifest_data.get('resources_dir', 'resources')

    def collect_plugins(self):
        plugin_info: dict
        for plugin_info, plugin_class in self.iterate_plugin_classes():
            instance = plugin_class(self)
            yield instance

    def iterate_plugin_classes(self) -> Generator[tuple[dict, Type[APlugin]], None, None]:
        plugin_info: dict
        if not self.manifest_file:
            raise PackageError(f"Package manifest file is not found")
        for plugin_info in self.iter_plugin_descriptions():
            for plugin in APlugin.load_from_manifest_data(plugin_info, self.manifest_file.as_posix()):
                if plugin:
                    yield plugin_info, plugin

    def iter_plugin_descriptions(self) -> Generator[list[dict[str, Any]], None, None]:
        plugins = self._manifest_data.get('plugins') or []
        if not isinstance(plugins, list):
            raise ValueError(f"Plugins must be a list")
        yield from plugins

    def get_requirements(self):
        required_packages = self._manifest_data.get('python_requirements') or {}
        if not isinstance(required_packages, dict):
            raise ValueError(f"Python requirements must be a dict")
        return required_packages

    def get_agio_requirements(self):
        required_packages = self._manifest_data.get('agio_packages_requirements') or {}
        if not isinstance(required_packages, dict):
            raise ValueError(f"agio requirements must be a dict")
        return required_packages

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

    @classmethod
    def from_path(cls, path: str) -> Self:
        if not cls.is_package_root(path):
            raise PackageError(f"Path is not a package root: {path}")
        manifest_file = Path(path, cls.manifest_file_name)
        manifest_data = cls._check_manifest_data(cls._load_manifest(manifest_file), manifest_file)
        return cls(manifest_data['name'], manifest_data['version'], path)
