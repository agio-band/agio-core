from __future__ import annotations
import logging
import os
from functools import cache, cached_property
from pathlib import Path
from typing import Any, Generator, Type

import yaml

from agio.core.entities import package
from agio.core.exceptions import PackageMetadataError, PackageError
from agio.core.plugins.base_plugin import APlugin
from agio.tools.modules import import_object_by_dotted_path

logger = logging.getLogger(__name__)


class APackageManager:
    """
    Manage local installed packages.
    """
    info_file_name = '__agio__.yml'

    def __init__(self, package_root: str|Path):
        self._root = Path(package_root)
        self._info_file = Path(package_root, self.info_file_name)
        self._info_data = self.__check_info_data(
            self.__load_info_file(
                self.__get_info_file(package_root)
            )
        )
        self._package = None

    def __repr__(self):
        return f'APackageManager({repr(self.package_name)})'

    # info file

    def __get_info_file(self, path: str | Path) -> Path:
        if not self.is_package_root(path):
            raise PackageError(f"Path is not a package root: {path}")
        info_file = Path(path, self.info_file_name)
        if not info_file.exists():
            raise PackageError(f"Manifest file not found: {info_file}")
        return info_file

    def __load_info_file(self, info_file: str | Path) -> dict:
        import yaml
        try:
            with open(info_file, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            raise PackageMetadataError(f"Metadata file not found: {info_file}")
        except yaml.YAMLError as e:
            raise PackageMetadataError(f"Error parsing info file: {e}")
        except Exception as e:
            raise PackageMetadataError(f"Error loading info file: {e}")

    def __check_info_data(self, info_data: dict) -> dict:
        # data is not empty
        if not info_data:
            raise PackageMetadataError(f"Manifest file is empty [{self._info_file}]")
        # data is dict
        if not isinstance(info_data, dict):
            raise PackageMetadataError(f"Manifest file is not a dictionary [{self._info_file}]")
        return info_data

    def get_meta_data_field(self, field_path: str, default = None) -> Any:
        parts = field_path.split('.')
        current_level = self._info_data.copy()
        while parts:
            next_part = parts.pop(0)
            if not isinstance(current_level, dict):
                raise PackageMetadataError(f'Wrong field_path {field_path}')
            current_level = current_level.get(next_part, None)
            if current_level is None:
                return default
        return current_level

    @property
    def info_file(self):
        return self.root / self.info_file_name

    def get_pacakge_metadata(self):
        return self._info_data

    # creators

    @classmethod
    def find_package_root(cls, path: str|Path) -> Path|None:
        try:
            meta_file = next(Path(path).rglob(cls.info_file_name))
            return meta_file.parent
        except StopIteration:
            return

    @classmethod
    def find_package(cls, path: str|Path) -> 'APackageManager'|None:
        pkg_root = cls.find_package_root(path)
        if pkg_root:
            return cls(pkg_root)

    @classmethod
    def is_package_root(cls, path: str) -> bool:
        info_file = os.path.join(path, cls.info_file_name)
        return os.path.exists(info_file)

    # props

    @property
    def root(self) -> Path:
        return self._root

    # from info file

    @cached_property
    def label(self):
        return self.get_meta_data_field('label')

    @cached_property
    def description(self):
        return self.get_meta_data_field('description', '').strip()

    @property
    def package_name(self):
        return self.get_meta_data_field('name')

    @property
    def package_version(self):
        return self.get_meta_data_field('version')

    @property
    def packages_dependencies(self):
        return self.get_meta_data_field('required_packages')

    @property
    def source_url(self):
        return self.get_meta_data_field('urls').get('source_url', None)

    @property
    def repository_api(self):
        return os.getenv('AGIO_FORCED_GIT_SERVICE') or self.get_meta_data_field('repository_api')

    # domains

    @cached_property
    def package(self):
        if self._package is None:
            pkg = package.APackage.find(self.package_name)
            if not pkg:
                raise PackageError(f'Pacakge not registered: {self.package_name}')
            self._package = pkg
        return self._package

    @cached_property
    def release(self):
        return self.package.get_release(self.package_version)

    # package content

    def get_resource_dir(self):
        return self.root / self._info_data.get('resources_dir', 'resources')

    def get_import_path(self, dotted_path: str) -> str:
        package_name = self.root.stem
        module_path = f"{package_name}.{dotted_path}"
        return module_path

    def collect_plugins(self):
        plugin_info: dict
        for plugin_info, plugin_class in self.iterate_plugin_classes():
            instance = plugin_class(self, plugin_info)
            yield instance

    def iterate_plugin_classes(self) -> Generator[tuple[dict, Type[APlugin]], None, None]:
        plugin_info: dict
        if not self.info_file.exists():
            raise PackageMetadataError(f"Package metafile file is not found")
        for plugin_info in self.iter_plugin_descriptions():
            for plugin in APlugin.load_from_info(plugin_info, self.info_file.as_posix()):
                if plugin:
                    yield plugin_info, plugin

    def iter_plugin_descriptions(self) -> Generator[list[dict[str, Any]], None, None]:
        plugins = self._info_data.get('plugins') or []
        if not isinstance(plugins, list):
            raise PackageMetadataError(f"Plugins must be a list")
        yield from plugins

    def get_workspace_settings_class(self):
        return self.get_settings_class('workspace')

    def get_local_settings_class(self):
        return self.get_settings_class('local')

    @cache
    def get_settings_class(self, settings_type: str):
        required = False
        settings_path = self.get_meta_data_field(f'settings.{settings_type}.model')
        if settings_path is None:
            # default path
            settings_path = f'package_settings.{settings_type}_settings.Settings'
        else:
            required = True
        import_path = self.get_import_path(settings_path)
        try:
            return import_object_by_dotted_path(*import_path.rsplit('.', 1))
        except (ModuleNotFoundError, AttributeError):
            if required:
                raise PackageError(f"Settings class not found: {settings_path}")

    def get_local_layout_config(self):
        return self.get_layout_configs('local')

    def get_workspace_layout_config(self):
        return self.get_layout_configs('workspace')

    def get_layout_configs(self, layout_type: str) -> dict | None:
        required = False
        rel_path = self.get_meta_data_field(f'settings.{layout_type}.layout')
        if rel_path is None:
            rel_path = f'package_settings/{layout_type}_layout.yml'
        else:
            required = True
        if not rel_path.strip():
            raise PackageMetadataError(f"Layout layout file not set or empty")
        layout_config_full_path = self.root / rel_path
        if not layout_config_full_path.exists():
            if required:
                raise PackageMetadataError(f"Layout config file for '{layout_type}' not found: {layout_config_full_path}")
            else:
                return
        if layout_config_full_path.is_dir():
            raise PackageMetadataError(f'Layout path is directory {layout_config_full_path}')
        with layout_config_full_path.open(encoding='utf-8') as layout_file:
            layout_config = yaml.safe_load(layout_file)
        self._expand_file_fields(layout_config)
        return layout_config

    def _expand_file_fields(self, values):

        def iter_params_wit_file_field(obj):
            if isinstance(obj, dict):
                if obj.get('local_file'):
                    yield obj
                for value in obj.values():
                    yield from iter_params_wit_file_field(value)
            elif isinstance(obj, list):
                for item in obj:
                    yield from iter_params_wit_file_field(item)

        for parm in iter_params_wit_file_field(values):
            file = Path(parm.get('local_file'))
            if not file.is_absolute():
                abs_path = self.root.joinpath(file).resolve()
                parm['abs_file']  = abs_path.as_posix()
            else:
                parm['abs_file'] = file.as_posix()

    def get_callbacks(self):
        callbacks = self.get_meta_data_field('callbacks') or []
        for path in callbacks:
            yield self.root.joinpath(path).with_suffix('.py').as_posix()

