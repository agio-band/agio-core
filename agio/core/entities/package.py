import logging
from typing import Generator, Self

from agio.core import api
from agio.core.api.utils import NOTSET
from .entity import Entity
from .package_release import APackageRelease

logger = logging.getLogger(__name__)


class APackage(Entity):
    type_name = "package"

    @classmethod
    def get_data(cls, entity_id: str) -> dict:
        return api.package.get_package(entity_id)

    @classmethod
    def create(cls, name: str) -> Self:
        package_id = api.package.create_package(name)
        return cls(package_id)

    def update(self,
               hidden: bool = NOTSET,
               disabled: bool = NOTSET,
               verified: bool = NOTSET,
               ) -> None:
        resp = api.package.update_package(
            self.id,
            hidden=hidden,
            disabled=disabled,
            verified=verified,
        )
        self._data.update(resp)

    @classmethod
    def iter(cls, limit: int = None) -> Generator[dict, None, None]:
        for pkg in api.package.iter_packages():
            yield cls(pkg)

    def delete(self) -> None:
        return api.package.delete_package(self.id)

    @classmethod
    def find(cls, name: str) -> Self|None:
        pkg = api.package.find_package(name)
        if pkg is not None:
            return cls(pkg)

    @property
    def name(self):
        return self._data["name"]

    def get_release(self, version: str) -> APackageRelease:
        return APackageRelease.find(self.name, version=version)

    def iter_releases(self) -> Generator[APackageRelease, None, None]:
        for release_data in api.package.iter_package_releases(self.id):
            yield APackageRelease(release_data)

    def latest_release(self) -> APackageRelease:
        revision_id = api.package.get_latest_release(self.id)
        if revision_id is not None:
            return APackageRelease(revision_id)


# class Package:
#     info_file_name = '__agio__.yml'
#
#     def __init__(self, name: str, version: str = None, installation_root: str|Path = None):
#         self._name = name
#         self._version = version
#         self._installation_root = installation_root
#         self._data = self._load_remote_data()
#         self._metadata = self._load_metadata()
#
#     def _get_info_file_path(self):
#         if self._installation_root:
#             return os.path.join(self._installation_root, self.info_file_name)
#
#     def _load_metadata(self):
#         info_file_path = self._get_info_file_path()
#         if not info_file_path or not os.path.isfile(info_file_path):
#             return {}
#
#     @classmethod
#     def get_from_workspace(cls, ws: AWorkspace, name: str):
#         for pkg in ws.iter_installed_packages():
#             pkg: APackage
#             if pkg.name == name:
#                 return pkg

    # @classmethod
    # def get_from_venv(cls, venv_path: str|Path, name: str):
    #     site_path = next(Path(venv_path).glob('lib/python*/site-packages'))
    #     if site_path and site_path.is_dir():
    #         pass
    #
    #
    # @classmethod
    # def get_from_path(cls, path: Path|str):
    #     pass



# class APackage:
#     """
#     Local package description
#     """
#     info_file_name = '__agio__.yml'
#
#     def __init__(self, package_root: str | Path):
#         self._root = Path(package_root)
#         self._info_file = Path(package_root, self.info_file_name)
#         self._info_data = self.__check_info_data(
#             self.__load_info_file(
#                 self.__get_info_file(package_root)
#             )
#         )
#
#     def __str__(self) -> str:
#         return f"{self.label} v{self.version}"
#
#     def __repr__(self) -> str:
#         return f"APackage({self.name} v{self.version})"
#
#     @property
#     def data(self):
#         return self._info_data
#
#     @property
#     def name(self) -> str:
#         return self._info_data['name']
#
#     @property
#     def label(self) -> str:
#         return self._info_data.get('label') or self.name
#
#     @property
#     def version(self) -> str:
#         return self._info_data['version']
#
#     @property
#     def icon_name(self) -> str | None:
#         return self._info_data.get('icon', None)
#
#     @property
#     def icon_path(self) -> str:
#         raise NotImplementedError
#
#     @property
#     def root(self):
#         return self._root
#
#     @property
#     def info_file(self):
#         return self.root / self.info_file_name
#
#     def get_resource_dir(self):
#         return self.root / self._info_data.get('resources_dir', 'resources')
#
#     def get_import_path(self, dotted_path: str) -> str:
#         package_name = self.root.stem
#         module_path = f"{package_name}.{dotted_path}"
#         return module_path
#
#     def collect_plugins(self):
#         plugin_info: dict
#         for plugin_info, plugin_class in self.iterate_plugin_classes():
#             instance = plugin_class(self, plugin_info)
#             yield instance
#
#     def iterate_plugin_classes(self) -> Generator[tuple[dict, Type[APlugin]], None, None]:
#         plugin_info: dict
#         if not self.info_file:
#             raise PackageError(f"Package manifest file is not found")
#         for plugin_info in self.iter_plugin_descriptions():
#             for plugin in APlugin.load_from_info(plugin_info, self.info_file.as_posix()):
#                 if plugin:
#                     yield plugin_info, plugin
#
#     def iter_plugin_descriptions(self) -> Generator[list[dict[str, Any]], None, None]:
#         plugins = self._info_data.get('plugins') or []
#         if not isinstance(plugins, list):
#             raise PackageRuntimeError(f"Plugins must be a list")
#         yield from plugins
#
#     def get_workspace_settings_class(self):
#         return self.get_settings_class('workspace')
#
#     def get_local_settings_class(self):
#         return self.get_settings_class('local')
#
#     def _get_meta_data_field(self, field_path: str) -> Any:
#         parts = field_path.split('.')
#         current_level = self._info_data.copy()
#         while parts:
#             next_part = parts.pop(0)
#             if not isinstance(current_level, dict):
#                 raise PackageRuntimeError(f'Wrong field_path {field_path}')
#             current_level = current_level.get(next_part, None)
#             if current_level is None:
#                 return None
#         return current_level
#
#     @cache
#     def get_settings_class(self, settings_type: str):
#         required = False
#         settings_path = self._get_meta_data_field(f'settings.{settings_type}.model')
#         if settings_path is None:
#             # default path
#             settings_path = f'package_settings.{settings_type}_settings.Settings'
#         else:
#             required = True
#         import_path = self.get_import_path(settings_path)
#         try:
#             return import_object_by_dotted_path(import_path)
#         except (ModuleNotFoundError, AttributeError):
#             if required:
#                 raise PackageError(f"Settings class not found: {settings_path}")
#
#     def get_local_layout_config(self):
#         return self.get_layout_configs('local')
#
#     def get_workspace_layout_config(self):
#         return self.get_layout_configs('workspace')
#
#     def get_layout_configs(self, layout_type: str) -> dict | None:
#         required = False
#         rel_path = self._get_meta_data_field(f'settings.{layout_type}.layout')
#         if rel_path is None:
#             rel_path = f'package_settings/{layout_type}_layout.yml'
#         else:
#             required = True
#         if not rel_path.strip():
#             raise PackageMetadataError(f"Layout layout file not set or empty")
#         layout_config_full_path = self.root / rel_path
#         if not layout_config_full_path.exists():
#             if required:
#                 raise PackageMetadataError(f"Layout config file for '{layout_type}' not found: {layout_config_full_path}")
#             else:
#                 return
#         if layout_config_full_path.is_dir():
#             raise PackageMetadataError(f'Layout path is directory {layout_config_full_path}')
#         with layout_config_full_path.open(encoding='utf-8') as layout_file:
#             layout_config = yaml.safe_load(layout_file)
#         return layout_config
#
#     def get_callbacks(self):
#         callbacks = self._get_meta_data_field('callbacks') or []
#         for path in callbacks:
#             yield self.root.joinpath(path).with_suffix('.py').as_posix()
#
#     @classmethod
#     def is_package_root(cls, path: str) -> bool:
#         info_file = os.path.join(path, "__agio__.yml")
#         return os.path.exists(info_file)
#
#     def __get_info_file(self, path: str | Path) -> Path:
#         if not self.is_package_root(path):
#             raise PackageError(f"Path is not a package root: {path}")
#         info_file = Path(path, self.info_file_name)
#         if not info_file.exists():
#             raise PackageError(f"Manifest file not found: {info_file}")
#         return info_file
#
#     def __load_info_file(self, info_file: str | Path) -> dict:
#         import yaml
#         try:
#             with open(info_file, 'r') as f:
#                 return yaml.safe_load(f)
#         except FileNotFoundError:
#             raise PackageError(f"Manifest file not found: {info_file}")
#         except yaml.YAMLError as e:
#             raise PackageError(f"Error parsing info file: {e}")
#         except Exception as e:
#             raise PackageError(f"Error loading info file: {e}")
#
#     def __check_info_data(self, info_data: dict) -> dict:
#         # data is not empty
#         if not info_data:
#             raise PackageMetadataError(f"Manifest file is empty [{self._info_file}]")
#         # data is dict
#         if not isinstance(info_data, dict):
#             raise PackageMetadataError(f"Manifest file is not a dictionary [{self._info_file}]")
#         return info_data


# class AReleaseInfo:
#     """
#     Package info from server
#     """
#     def __init__(self, release_data: dict):
#         self._data = release_data
#
#     @classmethod
#     def get_from_name_and_version(cls, package_name: str, version: str  = None):
#         return cls(api.package.get_package_release_by_name_and_version(package_name, version))
#
#     def __str__(self):
#         return f"{self.name} v{self.version}"
#
#     def __repr__(self):
#         return f"AReleaseInfo({self.name} v{self.version})"
#
#     @property
#     def data(self):
#         return self._data
#
#     @property
#     def name(self) -> str:
#         return self._data['package']['name']
#
#     @property
#     def version(self) -> str:
#         return self._data['name']
#
#     @property
#     def source_url(self) -> str:
#         """Source code repository url"""
#         return self._data['urls'].get('source_url')
#
#     def get_assets(self):
#         return self._data.get('assets', {}).get('whl', [])
#
#     def get_installation_command(self):
#         STORE_DOMAIN = "???"     # TODO
#         if assets := self.get_assets():
#             url_list = [asset['url'] for asset in assets]
#             cmd = filter_compatible_package(url_list)
#             cmd = cmd.strip()
#             if not cmd:
#                 raise PackageError(f"Error fetching whl file, Compatible asset not found")
#             if cmd.startswith('http'):
#                 url_info = urlparse(cmd)
#                 if url_info.netloc == STORE_DOMAIN:
#                     logger.info(f'Downloading release from store {cmd}')
#                     cmd = download_file(
#                         cmd,
#                         Path(app_dirs.temp_dir(), 'releases').as_posix(),
#                         Path(cmd).name, use_credentials= True
#                     )
#                 # else:
#                 #     cmd = f'git+{cmd}'
#             elif cmd.startswith('git+'):
#                 pass
#             else:
#                 cmd = os.path.expandvars(Path(cmd).expanduser())
#                 if not os.path.exists(cmd):
#                     raise PackageError(f"Error fetching package {self}, file not found: {cmd}")
#             return cmd
#         elif self.source_url:
#             cmd = os.path.expandvars(Path(self.source_url).expanduser())
#         else:
#             raise PackageError(f"Error fetching package {self}, installation command not created")
#         return cmd

