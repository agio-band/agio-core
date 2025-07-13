import json
import os
import shutil
import sys
from functools import cached_property, lru_cache
from pathlib import Path
from uuid import UUID

from agio.core.exceptions import WorkspaceNotExists, WorkspaceNotInstalled
from agio.core.packages.package import APackage, AReleaseInfo, logger
from agio.core.settings import WorkspaceSettingsHub
from agio.core.utils import config
from agio.core.workspace import pkg_manager, venv_utils
from agio.core import api
from agio.core.events import emit


class AWorkspace:
    _meta_file_name = '__agio_ws__.json'
    workspaces_root = Path(config.workspace.WORKSPACES_CACHE_ROOT).expanduser()

    def __init__(self, workspace_id: str | UUID):
        self.id = workspace_id
        self._root = self.workspaces_root.joinpath(str(self.id))
        self._packages = None
        try:
            self._data = self._load_local_data()
        except WorkspaceNotInstalled:
            self._data = self._load_remote_data()

    def __str__(self):
        return self.name or self.id

    def __repr__(self):
        return f'<Workspace "{str(self)}">'

    @lru_cache
    def packages(self) -> list[APackage]:
        if self._packages is None:
            if self.root.exists():
                self._packages = tuple(self.iter_installed_packages())
        return self._packages

    @property
    def local_meta_file(self):
        return self.root / self._meta_file_name

    def _load_local_data(self):
        meta_file = self.local_meta_file
        if not meta_file.exists():
            raise WorkspaceNotInstalled('Workspace not installed locally')
        with open(meta_file) as f:
            return json.load(f)

    def _load_remote_data(self):
        return api.workspace.get_workspace(self.id)

    @classmethod
    def current(cls):
        current_workspace_id = os.getenv('AGIO_CURRENT_WORKSPACE')
        if not current_workspace_id:
            return
        return cls(current_workspace_id)

    @property
    def name(self):
        return self._data.get('name')

    @property
    def root(self):
        return self._root

    @cached_property
    def venv_manager(self):
        return pkg_manager.get_package_manager(self.root)

    # packages

    def iter_installed_packages(self):
        yield from self.venv_manager.iter_packages()

    # def iter_packages(self):
    #     """
    #     Iter installed packages
    #     """
    #     if not self.is_installed():
    #         raise WorkspaceNotInstalled
    #     for pkg in self._packages:
    #         yield APackage(**pkg)

    def get_package(self, package_name) -> APackage:
        pkg_data = self._data.get(package_name)
        if not pkg_data:
            raise ValueError(f'Package {package_name} not found in workspace {self.id}')
        return APackage(**pkg_data)

    def get_launch_envs(self):
        env = {
            'AGIO_WORKSPACE_ID': str(self.id),
            'VIRTUAL_ENV': self.root.as_posix()
        }
        emit('core.workspace.launch_envs', {'envs': env, 'workspace': self})
        return env

    def get_pyexecutable(self) -> str:
        return self.venv_manager.python_executable

    # def collect_stat(self):
    #     """
    #     File sizes
    #     Creation date
    #     Package count
    #         python libs
    #         agio packages
    #     """
    #     pass

    def exists(self):
        return self.root.exists()

    def is_installed(self):
        return self.local_meta_file.exists()

    def need_to_reinstall(self):
        if self.is_installed():
            os_name = sys.platform.lower()
            required_py_version = self._data.get('python_version', {}).get(os_name)
            if required_py_version:
                current_version = self.venv_manager.get_python_version(full=True)
                if not venv_utils.check_current_python_version(
                        required_py_version,
                        current_version):
                    return True
        else:
            return True

    def install(self, clean: bool = False, no_cache: bool = False):
        emit('core.workspace.before_install', {'workspace': self})
        self._data = self._load_remote_data()
        reinstall = clean or self.need_to_reinstall()

        if reinstall:
            os_name = sys.platform.lower()
            logger.info('Reinstalling workspace...')
            if self.is_installed():
                self.remove()
            py_version_required = self._data.get('python_version', {}).get(os_name)
            self.venv_manager.create_venv(py_version_required)

        package_info_list = self.get_packages_info()
        install_args = [pkg.get_installation_command() for pkg in package_info_list]
        # debug message
        print('-'*100)
        print('Python version:', self.venv_manager.get_python_version())
        print('-'*100)
        for pkg in install_args:
            print(pkg)
        print('-'*100)

        self.venv_manager.install_packages(*install_args, no_cache=no_cache)
        with open(self.local_meta_file, 'w') as f:
            json.dump(self._data, f, indent=4)
        emit('core.workspace.installed', {'workspace': self, 'data': self._data, 'meta_filename': self.local_meta_file})

    def get_packages_info(self):
        return [AReleaseInfo(pkg['name'], pkg['version']) for pkg in self._packages]

    def remove(self) -> bool:
        emit('core.workspace.before_remove', {'workspace': self})
        if self.exists():
            self.venv_manager.delete_venv()
            shutil.rmtree(self.root)
            emit('core.workspace.removed', {'workspace': self})
            return True
        return False

    def reinstall(self):
        self.remove()
        self.install()

    def update(self):
        if not self.exists():
            raise WorkspaceNotExists('Workspace not installed')
        self.install()

    def get_settings(self) -> WorkspaceSettingsHub:
        settings_data = {}  # TODO
        # create workspace settings instance with applied values
        settings = WorkspaceSettingsHub(settings_data)
        emit('core.settings.workspace_settings_loaded', {'settings': settings, 'workspace': ws})
        return settings

