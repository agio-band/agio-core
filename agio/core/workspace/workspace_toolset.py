import json
import shutil
import sys
from functools import cached_property
from pathlib import Path
from typing import Self

from agio.core import api
from agio.core.events import emit
from agio.core.exceptions import WorkspaceNotInstalled
from agio.core.utils import config
from agio.core.workspace import AWorkspace, pkg_manager, venv_utils
from agio.core.workspace.revision import AWorkspaceRevision


class AWorkspaceToolset:
    _meta_file_name = '__agio_ws__.json'
    workspaces_root = Path(config.WS.CACHE_ROOT).expanduser()
    WORKSPACE_ENV_NAME = 'AGIO_WORKSPACE_ID'
    REVISION_ENV_NAME = 'AGIO_WORKSPACE_REVISION_ID'

    def __init__(self, revision: AWorkspaceRevision):
        if revision is not None:
            if isinstance(revision, str):
                revision = AWorkspaceRevision(revision)
        self._revision = revision

    def get_workspace(self) -> AWorkspace:
        return AWorkspace(self._data['workspaceId'])

    @classmethod
    def from_workspace(cls, workspace: AWorkspace|str) -> Self:
        if isinstance(workspace, str):
            data = api.workspace.get_revision_by_workspace_id(workspace)
            revision = AWorkspaceRevision(data)
            return cls(revision)
        elif isinstance(workspace, AWorkspace):
            current_revision = workspace.get_current_revision()
            if not current_revision:
                raise Exception(f"No current revision found for workspace {workspace}")
            return cls(current_revision)

    # meta file

    @property
    def local_meta_file(self):
        return self.install_root / self._meta_file_name

    def _load_local_data(self):
        meta_file = self.local_meta_file
        if not meta_file.exists():
            raise WorkspaceNotInstalled('Workspace not installed locally')
        with meta_file.open() as f:
            return json.load(f)

    def get_meta_value(self, key: str, default=None):
        return self._data['workspace'].get('metadata', {}).get(key, default)

    # props

    @property
    def revision(self):
        return self._revision

    @property
    def root(self):
        config.WS.CACHE_ROOT
        return self._root

    @property
    def install_root(self):
        return self.root.joinpath(self.revision_id)

    # install and manage

    @cached_property
    def venv_manager(self):
        return pkg_manager.get_package_manager(self.install_root)



    def install(self, clean: bool = False, no_cache: bool = False):
        emit('core.workspace.before_install', {'workspace': self})
        self._data = self._load_remote_data()

        package_info_list = self.get_packages_info()
        if not package_info_list:
            raise Exception('No packages to install')
        install_args = [pkg.get_installation_command() for pkg in package_info_list]

        reinstall = clean or self.need_to_reinstall()

        if reinstall:
            os_name = sys.platform.lower()
            logger.info('Reinstalling workspace...')
            if self.is_installed():
                self.remove()
            py_version_required = self._data.get('python_version', {}).get(os_name)
            self.venv_manager.create_venv(py_version_required)


        # debug message
        print('-'*100)
        print('Python version:', self.venv_manager.get_python_version())
        print('-'*100)
        for pkg in install_args:
            print(pkg)
        print('-'*100)

        logger.info(f'Packages to install: {package_info_list}')
        self.venv_manager.install_packages(*install_args, no_cache=no_cache)
        with open(self.local_meta_file, 'w') as f:
            json.dump(self._data, f, indent=4)
        emit('core.workspace.installed', {'workspace': self, 'data': self._data, 'meta_filename': self.local_meta_file})


    def iter_installed_packages(self):
        yield from self.venv_manager.iter_packages()

    def is_installed(self):
        return self.local_meta_file.exists()
    def need_to_reinstall(self):
        if self.is_installed():
            os_name = sys.platform.lower()
            required_py_version = self.get_meta_value('python_version', {}).get(os_name)
            if required_py_version:
                current_version = self.venv_manager.get_python_version(full=True)
                if not venv_utils.check_current_python_version(
                        required_py_version,
                        current_version):
                    return True
        # TODO: check module list hash
        else:
            return True

    def remove(self) -> bool:
        emit('core.workspace.before_remove', {'workspace': self})
        if self.exists():
            self.venv_manager.delete_venv()
            shutil.rmtree(self.install_root)
            emit('core.workspace.removed', {'workspace': self})
            return True
        return False

    # launch
    def get_pyexecutable(self) -> str:
        return self.venv_manager.python_executable

    def get_launch_envs(self):
        env = {
            self.WORKSPACE_ENV_NAME: str(self.id),
            self.REVISION_ENV_NAME: str(self.revision_id),
            'VIRTUAL_ENV': self.install_root.as_posix()
        }
        emit('core.workspace.launch_envs', {'envs': env, 'workspace': self})
        return env
