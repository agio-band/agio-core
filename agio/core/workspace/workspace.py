import json
import os
import shutil
import sys
from functools import cached_property
from pathlib import Path
from uuid import UUID

from agio.core.exceptions import WorkspaceNotExists, WorkspaceNotInstalled
from agio.core.packages.package import APackage, AReleaseInfo
# from agio.core.packages.package_tools import resolve_and_simplify_dependencies
from agio.core.workspace import pkg_manager, request_data


class AWorkspace:
    _meta_file_name = '__agio_ws__.json'
    workspaces_root = Path('~/.agio/workspaces').expanduser()  # TODO: path from config

    def __init__(self, workspace_id: str | UUID):
        self.id = workspace_id
        self._root = self.workspaces_root.joinpath(str(self.id))
        try:
            self._data = self._load_local_data()
        except WorkspaceNotInstalled:
            self._data = self._load_remote_data()

    def __str__(self):
        return self.name or self.id

    def __repr__(self):
        return f'<Workspace "{str(self)}">'

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
        data = request_data.get_workspace_data(self.id)
        return data

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

    # def get_package_list_to_install(self) -> list:
    #     packages = []
    #     for pkg in self._data.get('packages', []):
    #         packages.append(pkg)
    #     return packages

    # packages

    def iter_installed_packages(self):
        yield from self.venv_manager.iter_packages()

    def iter_packages(self):
        if not self.is_installed():
            raise WorkspaceNotInstalled
        for pkg in self._data.get('packages', []):
            yield APackage(**pkg)

    def get_launch_envs(self):
        return {
            'AGIO_WORKSPACE_ID': str(self.id),
            'VIRTUAL_ENV': self.root.as_posix()
        }

    def get_pyexecutable(self) -> str:
        return self.venv_manager.python_executable

    def collect_stat(self):
        """
        File sizes
        Creation date
        Package count
            python libs
            agio packages
        """
        pass

    def exists(self):
        return self.root.exists()

    def is_installed(self):
        return self.local_meta_file.exists()

    def install(self, clean: bool = False, no_cache: bool = False):
        self._data = self._load_remote_data()
        if self.is_installed():
            # TODO check current version info
            if clean:
                self.venv_manager.delete_venv()
        else:
            os_name = sys.platform.lower()
            self.venv_manager.create_venv(self._data.get('python_version', {}).get(os_name))
        from pprint import pprint
        package_info_list = self.get_packages_info()
        install_args = [pkg.get_installation_command() for pkg in package_info_list]      # todo: move to multithread
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

    def get_packages_info(self):
        return [AReleaseInfo(pkg['name'], pkg['version']) for pkg in self._data['packages']]

    def remove(self) -> bool:
        if self.exists():
            self.venv_manager.delete_venv()
            shutil.rmtree(self.root)
            return True
        return False

    def reinstall(self):
        self.remove()
        self.install()

    def update(self):
        if not self.exists():
            raise WorkspaceNotExists('Workspace not installed')
        self.install()

