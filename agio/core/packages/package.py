import os
import shutil
from pathlib import Path
from typing import Generator, Type, Any

from agio.core.exceptions import PackageError
from agio.core.plugins.plugin_base import APlugin
from agio.core.utils import process_tools
from agio.core.workspace.pkg_manager import get_package_manager_class


class APackage:
    """
    Local package description
    """
    manifest_file_name = '__agio__.yml'

    def __init__(self, package_root: str | Path):
        self._root = Path(package_root)
        self._manifest_file = Path(package_root, self.manifest_file_name)
        self._manifest_data = self.__check_manifest_data(
            self.__load_manifest_file(
                self.__get_manifest_file(package_root)
            )
        )

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
        return self.root / self.manifest_file_name

    @property
    def installation_name(self):
        return f'{self.name}=={self.version}'

    def get_resource_dir(self):
        return self.root / self._manifest_data.get('resources_dir', 'resources')

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

    def __get_manifest_file(self, path: str | Path) -> Path:
        if not self.is_package_root(path):
            raise PackageError(f"Path is not a package root: {path}")
        manifest_file = Path(path, self.manifest_file_name)
        if not manifest_file.exists():
            raise PackageError(f"Manifest file not found: {manifest_file}")
        return manifest_file

    def __load_manifest_file(self, manifest_file: str | Path) -> dict:
        import yaml
        try:
            with open(manifest_file, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            raise PackageError(f"Manifest file not found: {manifest_file}")
        except yaml.YAMLError as e:
            raise PackageError(f"Error parsing manifest file: {e}")
        except Exception as e:
            raise PackageError(f"Error loading manifest file: {e}")

    def __check_manifest_data(self, manifest_data: dict) -> dict:
        # manifest is not empty
        if not manifest_data:
            raise ValueError(f"Manifest file is empty [{self._manifest_file}]")
        # manifest data is dict
        if not isinstance(manifest_data, dict):
            raise ValueError(f"Manifest file is not a dictionary [{self._manifest_file}]")
        # required fields exists and not empty
        required_fields = ('name', 'label', 'version', 'repository_url')
        for field in required_fields:
            if field not in manifest_data:
                raise ValueError(f"Manifest file is missing required field: {field} [{self._manifest_file}]")
            if not manifest_data[field]:
                raise ValueError(f"Manifest field {field} is empty [{self._manifest_file}]")
        return manifest_data

