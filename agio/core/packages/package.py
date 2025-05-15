import os
import re
from functools import lru_cache, cached_property
from pathlib import Path
from typing import Generator, Type, Any
import logging
from urllib.parse import urlparse
import yaml

from agio.core.exceptions import PackageError
from agio.core.plugins.plugin_base import APlugin
from agio.core.utils import git_utils
from agio.core.utils.network import download_file
from agio.core.utils.import_utils import import_object_by_dotted_path
from agio.core.utils.repository_utils import fetch_whl_url, filter_compatible_package
from agio.core.workspace.request_data import get_package, get_release

logger = logging.getLogger(__name__)

STORE_HOST = 'http://localhost:8002'


class APackage:
    """
    Local package description
    """
    info_file_name = '__agio__.yml'

    def __init__(self, package_root: str | Path):
        self._root = Path(package_root)
        self._info_file = Path(package_root, self.info_file_name)
        self._info_data = self.__check_info_data(
            self.__load_info_file(
                self.__get_info_file(package_root)
            )
        )

    def __str__(self) -> str:
        return f"{self.label} v{self.version}"

    def __repr__(self) -> str:
        return f"APackage({self.name} v{self.version})"

    @property
    def data(self):
        return self._info_data

    @property
    def name(self) -> str:
        return self._info_data['name']

    @property
    def label(self) -> str:
        return self._info_data.get('label') or self.name

    @property
    def version(self) -> str:
        return self._info_data['version']

    @property
    def icon_name(self) -> str | None:
        return self._info_data.get('icon', None)

    @property
    def icon_path(self) -> str:
        raise NotImplementedError

    @property
    def root(self):
        return self._root

    @property
    def info_file(self):
        return self.root / self.info_file_name

    def get_resource_dir(self):
        return self.root / self._info_data.get('resources_dir', 'resources')

    def import_path(self, dotted_path: str) -> str:
        package_name = self.root.stem
        module_path = f"{package_name}.{dotted_path}"
        return module_path

    def collect_plugins(self):
        plugin_info: dict
        for plugin_info, plugin_class in self.iterate_plugin_classes():
            instance = plugin_class(self)
            yield instance

    def iterate_plugin_classes(self) -> Generator[tuple[dict, Type[APlugin]], None, None]:
        plugin_info: dict
        if not self.info_file:
            raise PackageError(f"Package manifest file is not found")
        for plugin_info in self.iter_plugin_descriptions():
            for plugin in APlugin.load_from_info(plugin_info, self.info_file.as_posix()):
                if plugin:
                    yield plugin_info, plugin

    def iter_plugin_descriptions(self) -> Generator[list[dict[str, Any]], None, None]:
        plugins = self._info_data.get('plugins') or []
        if not isinstance(plugins, list):
            raise ValueError(f"Plugins must be a list")
        yield from plugins

    def get_workspace_settings_class(self):
        return self._get_settings_class('workspace')

    def get_local_settings_class(self):
        return self._get_settings_class('local')

    def _get_settings_class(self, settings_type: str):
        required = True
        settings_path = self._info_data.get('settings', {}).get(settings_type)
        if not settings_path:
            required = False
            settings_path = self.import_path(f'settings.{settings_type}.Settings')
        try:
            cls = import_object_by_dotted_path(settings_path)
        except ModuleNotFoundError:
            if not required:
                return None
            raise PackageError(f"Settings class not found: {settings_path}")
        return cls

    @classmethod
    def is_package_root(cls, path: str) -> bool:
        info_file = os.path.join(path, "__agio__.yml")
        return os.path.exists(info_file)

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
            raise PackageError(f"Manifest file not found: {info_file}")
        except yaml.YAMLError as e:
            raise PackageError(f"Error parsing info file: {e}")
        except Exception as e:
            raise PackageError(f"Error loading info file: {e}")

    def __check_info_data(self, info_data: dict) -> dict:
        # data is not empty
        if not info_data:
            raise ValueError(f"Manifest file is empty [{self._info_file}]")
        # data is dict
        if not isinstance(info_data, dict):
            raise ValueError(f"Manifest file is not a dictionary [{self._info_file}]")
        return info_data

STORE_DOMAIN =  'localhost:8082'    # TODO

class AReleaseInfo:
    """
    Package info from server
    """
    def __init__(self, package_name: str, version: str  = None):
        self._package_info = get_release(package_name, version)

    def __str__(self):
        return f"{self.name} v{self.version}"

    def __repr__(self):
        return f"AReleaseInfo({self.name} v{self.version})"

    @property
    def data(self):
        return self._package_info

    @property
    def name(self) -> str:
        return self._package_info['name']

    @property
    def version(self) -> str:
        return self._package_info['version']

    @property
    def source_url(self) -> str:
        return self._package_info['urls'].get('source_url')

    def get_assets(self):
        return self._package_info.get('assets', [])

    def get_installation_command(self):
        if assets := self.get_assets():
            url_list = [asset['url'] for asset in assets]
            cmd = filter_compatible_package(url_list)
            cmd = cmd.strip()
            if not cmd:
                raise PackageError(f"Error fetching whl file, Compatible asset not found")
            if cmd.startswith('http'):
                url_info = urlparse(cmd)
                if url_info.netloc == STORE_DOMAIN:
                    logger.info(f'Downloading release from store {cmd}')
                    cmd = download_file(
                        cmd, config['TEMP_DIR'] / 'releases', Path(cmd).name, use_credentials= True
                    )
                # else:
                #     cmd = f'git+{cmd}'
            elif cmd.startswith('git+'):
                pass
            else:
                cmd = os.path.expandvars(Path(cmd).expanduser())
                if not os.path.exists(cmd):
                    raise PackageError(f"Error fetching package {self}, file not found: {cmd}")
            return cmd
        elif self.source_url:
            cmd = os.path.expandvars(Path(self.source_url).expanduser())
        else:
            raise PackageError(f"Error fetching package {self}, installation command not created")
        return cmd


class APackageRepository:
    def __init__(self, root: str|Path):
        self.root = Path(root)

    @property
    def source_url(self):
        url = git_utils.get_remote_url(self.root.as_posix())
        if not url:
            url = self.data['urls'].get('source_url')
        url = re.sub(r'\.git$', '', url)
        return url

    @property
    def repository_api(self):
        if api_type := self.data.get('repository_api'):
            return api_type

    @property
    def release_repository_url(self):
        if self.data.get('private_releases'):
            return STORE_HOST + '/releases'
        else:
            return self.source_url

    @property
    def version(self):
        return self.data['version']

    @property
    def name(self):
        return self.data['name']

    @property
    def label(self):
        return self.data['label']

    @cached_property
    def data(self):
        agio_info_file = self.get_info_file_path()
        if not agio_info_file or not agio_info_file.exists():
            raise Exception(f"Package info file not found: {agio_info_file}")
        with open(agio_info_file, 'r') as f:
            agio_data = yaml.safe_load(f)
        return agio_data

    @lru_cache
    def get_info_file_path(self) -> Path:
        main_meta_file = next(self.root.rglob('__agio__.yml'), None)
        if not main_meta_file:
            raise FileNotFoundError(f"Main info file not found: {self.root}")
        logger.debug('Main info file: %s', main_meta_file)
        return main_meta_file
