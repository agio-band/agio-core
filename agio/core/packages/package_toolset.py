import logging
import os
import re
from functools import cache, cached_property
from pathlib import Path
from typing import Any, Generator, Type, Self
from urllib.parse import urlparse

import yaml

from agio.core.utils import config, git_utils
from agio.core.exceptions import PackageMetadataError, PackageError, PackageLoadingError, PackageRepositoryError
from agio.core.plugins.plugin_base import APlugin
from agio.core.utils import app_dirs
from agio.core.utils.import_utils import import_object_by_dotted_path
from agio.core.utils.network import download_file
from agio.core.utils.repository_utils import filter_compatible_package
from .release import APackageRelease
from .package import APackage
from agio.core.workspace.pkg_manager import get_package_manager
from ..plugins.base.remote_repository_base import RemoteRepositoryPlugin

logger = logging.getLogger(__name__)


class APackageLocal:
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

    def _get_meta_data_field(self, field_path: str, default = None) -> Any:
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

    def get_info_file(self):
        return self.root / self.info_file_name
    # creators

    @classmethod
    def find_package_root(cls, path: str|Path) -> Path|None:
        try:
            meta_file = next(Path(path).rglob(cls.info_file_name))
            return meta_file.parent
        except StopIteration:
            return

    @classmethod
    def find_package(cls, package_root: str|Path) -> Self|None:
        pkg_root = cls.find_package_root(package_root)
        if pkg_root:
            return cls(pkg_root)

    @classmethod
    def is_package_root(cls, path: str) -> bool:
        info_file = os.path.join(path, "__agio__.yml")
        return os.path.exists(info_file)

    # props

    @property
    def root(self) -> Path:
        return self._root

    @cached_property
    def version(self):
        return self._get_meta_data_field('version')

    @cached_property
    def name(self):
        return self._get_meta_data_field('name')

    @cached_property
    def label(self):
        return self._get_meta_data_field('label')

    @cached_property
    def description(self):
        return self._get_meta_data_field('description')

    @cached_property
    def package(self):
        if self._package is None:
            pkg = APackage.find(self.package_name)
            if not pkg:
                raise PackageError(f'Pacakge not registered: {self.package_name}')
            self._package = pkg
        return self._package

    @cached_property
    def release(self):
        return self.package.get_release(self.package_version)

    @property
    def package_name(self):
        return self._get_meta_data_field('name')

    @property
    def package_version(self):
        return self._get_meta_data_field('version')

    @property
    def python_dependencies(self):
        return self._get_meta_data_field('dependencies')

    @property
    def packages_dependencies(self):
        return self._get_meta_data_field('agio_dependencies')

    @property
    def source_url(self):
        return self._get_meta_data_field('urls').get('source_url', None)

    @property
    def repository_api(self):
        return self._get_meta_data_field('repository_api')

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
        if not self.get_info_file():
            raise PackageMetadataError(f"Package metafile file is not found")
        for plugin_info in self.iter_plugin_descriptions():
            for plugin in APlugin.load_from_info(plugin_info, self.get_info_file().as_posix()):
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
        settings_path = self._get_meta_data_field(f'settings.{settings_type}.model')
        if settings_path is None:
            # default path
            settings_path = f'package_settings.{settings_type}_settings.Settings'
        else:
            required = True
        import_path = self.get_import_path(settings_path)
        try:
            return import_object_by_dotted_path(import_path)
        except (ModuleNotFoundError, AttributeError):
            if required:
                raise PackageError(f"Settings class not found: {settings_path}")

    def get_local_layout_config(self):
        return self.get_layout_configs('local')

    def get_workspace_layout_config(self):
        return self.get_layout_configs('workspace')

    def get_layout_configs(self, layout_type: str) -> dict | None:
        required = False
        rel_path = self._get_meta_data_field(f'settings.{layout_type}.layout')
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
        return layout_config

    def get_callbacks(self):
        callbacks = self._get_meta_data_field('callbacks') or []
        for path in callbacks:
            yield self.root.joinpath(path).with_suffix('.py').as_posix()

    def get_installation_command(self):
        release = self.get_release()
        if assets := release.get_assets():
            url_list = [asset['url'] for asset in assets]
            cmd = filter_compatible_package(url_list)
            cmd = cmd.strip()
            if not cmd:
                raise PackageError(f"Error fetching whl file, Compatible asset not found")
            if cmd.startswith('https'):
                # check if is private package saved on private store
                url_info = urlparse(cmd)
                if url_info.netloc == urlparse(config.PKG.STORE_URL).netloc:
                    logger.info(f'Downloading release from store {cmd}')
                    cmd = download_file(
                        cmd,
                        Path(app_dirs.temp_dir(), 'releases').as_posix(),
                        Path(cmd).name, use_credentials=True
                    )
            elif cmd.startswith('git+'):
                pass
            else:
                cmd = os.path.expandvars(Path(cmd).expanduser())
                if not os.path.exists(cmd):
                    raise PackageError(f"Error fetching package {self}, file not found: {cmd}")
            return cmd
        elif self.get_source_url():
            cmd = os.path.expandvars(Path(self.get_source_url()).expanduser())
        else:
            raise PackageError(f"Error fetching package {self}, installation command not created")
        return cmd


class APackageRepository:
    """
    Manage package repository
    """
    def __init__(self, repository_root: str|Path):
        self.root = Path(repository_root)
        if not self.repository_is_valid():
            raise PackageRepositoryError(f"Repository '{repository_root}' is not valid")

    def repository_is_valid(self):
        return self.root.is_dir() and self.root.joinpath('.git').exists()

    @cached_property
    def local_pkg(self):
        return APackageLocal.find_package(self.root)

    @cached_property
    def remote_repository(self) -> RemoteRepositoryPlugin:
        return get_remote_repository_plugin(self.local_pkg.source_url, self.local_pkg.repository_api)

    @property
    def origin(self):
        return git_utils.get_remote_url(self.root.as_posix())

    def make_release(self, **kwargs):
        """
        Make and register a new release from current version.
        """
        # check package registered
        if not self.local_pkg.package:
            raise PackageError(f"Package '{self.local_pkg.package_name}' not registered")
        # check release version is already exists
        if self.local_pkg.release:
            raise ValueError(f"Release {self.local_pkg.package_name} {self.local_pkg.package_version} "
                             f"already exists in agio repository")
        # check unsaved changes
        if not kwargs.get('no_check_branch', False):
            active_branch = git_utils.get_current_branch(self.root.as_posix())
            if active_branch not in ('main', 'master'):
                raise ValueError(f"Branch is not main or master ({active_branch})")
        else:
            logger.debug('Skip branch check')
        # check uncommited changes
        if not kwargs.get('no_check_commits', False):
            if git_utils.has_uncommited_changes(self.root.as_posix()):
                raise ValueError(f"Has uncommited changes")
        else:
            logger.debug('Skip uncommited changes check')
        # check unpushed commits
        if not kwargs.get('no_check_pushed', False):
            if git_utils.has_unpushed_commits(self.root.as_posix()):
                raise ValueError(f"Has unpushed commits")
        else:
            logger.debug('Skip unpushed commits check')
        # check version is not exists in remote
        access_data = kwargs.get('access_data', {})
        local_tags, remote_tags = git_utils.get_tags(self.root.as_posix(), self.origin)
        if self.local_pkg.package_version in remote_tags:
            if self.remote_repository.get_release_with_tag(self.local_pkg.source_url, self.local_pkg.package_version, access_data):
                raise ValueError(f"Version {self.local_pkg.package_name} already exists in remote repository")
        # build
        build_path = self.build(**kwargs)
        # create release on remote repository
        self.remote_repository.create_and_upload_release(
            self.local_pkg.source_url,
            self.local_pkg.version,
            build_path,
        )
        release = self.remote_repository.get_release_with_tag(
            self.local_pkg.source_url,
            self.local_pkg.package_version,
            access_data)
        if not release:
            raise Exception(
                f"Release {self.local_pkg.package_name} {self.local_pkg.package_version} not found in repository"
            )
        if not release.get('assets'):
            raise Exception(f"Release {self.local_pkg.package_version} has no assets")
        assets = []
        for ast in release['assets']:
            assets.append(dict(
                name=ast['name'],
                size=ast['size'],
                url=ast['browser_download_url'],
            ))
        self.register_release(assets)
        release_data = dict(
            release_url=release['html_url'],
            assets=assets,
            version=self.local_pkg.package_version,
            release_id=release['id'],
            created_at=release['created_at'],
        )
        return release_data

    @cached_property
    def package_manager(self):
        return get_package_manager(self.root)

    def build(self, **kwargs):
        return self.package_manager.build_package(**kwargs)

    def register_release(self, assets: list, metadata: dict = None):
        release = APackageRelease.create(
            package_id=self.local_pkg.package.id,
            version=self.local_pkg.package_version,
            label=self.local_pkg.label,
            description=self.local_pkg.description,
            assets={"whl": assets},
            metadata=metadata,
            # icon
        )
        return release

    def remove_release(self):
        pass



def get_remote_repository_plugin(repo_url: str, repository_api: str = None):
    from agio.core import plugin_hub

    if not repo_url:
        raise PackageLoadingError('No repo url provided')
    for plugin in plugin_hub.get_plugins_by_type('remote_repository'):
        if repository_api and repository_api == plugin.repository_api:
            return plugin
        if plugin.check_is_valid_url(repo_url):
            return plugin
    raise PackageLoadingError(f'No Release repository plugin found for url: {repo_url}. '
                              f'Use meta variable "repository_api" in __agio__.yml file '
                              f'to specify the repository API manually.')
