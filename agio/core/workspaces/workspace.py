import copy
import json
import logging
import os
import shutil
import sys
import time
from datetime import datetime
from functools import cached_property, cache
from pathlib import Path

from agio.core import api, env_names
from agio.core.entities import AWorkspaceRevision, AWorkspace, APackageRelease, APackage
from agio.core.events import emit
from agio.core.exceptions import WorkspaceNotInstalled, WorkspaceNotExists, NotExistsError
from agio.core.config import config
from agio.tools import pkg_manager, app_dirs
from agio.tools.launching import LaunchContext
from agio.tools.packaging_tools import collect_packages_to_install
from agio.tools.venv_helpers import check_current_python_version

logger = logging.getLogger(__name__)


class DefaultWorkspaceError(Exception):
    pass


class AWorkspaceManager:
    """Manage workspaces on local host"""
    _meta_file_name = '__agio_ws__.json'
    workspaces_root = Path(config.WS.INSTALL_DIR).expanduser()
    default_python_version = '>=3.11'

    def __init__(self, revision: AWorkspaceRevision|str|dict = None, root: str|Path = None, **kwargs):
        self._install_root = root
        self._revision = None
        if revision is not None:
            if isinstance(revision, (str, dict)):
                self._revision = AWorkspaceRevision(revision)
            elif isinstance(revision, AWorkspaceRevision):
                self._revision = revision
            else:
                raise TypeError('Invalid revision type')
        if not root and not revision:
            raise TypeError('Root directory or revision must be specified')
        self._kwargs = kwargs
        self._extra_launch_envs = {}

    def __repr__(self):
        if self._revision:
            return f'<{self.__class__.__name__} revision={self._revision.id}>'
        else:
            return f'<{self.__class__.__name__} NO-REVISION>'

    @property
    def extra_launch_envs(self) -> dict:
        return self._kwargs.get('launch_envs', {})

    @property
    def root_suffix(self) -> str:
        return str(self._kwargs.get('root_suffix', '')) or os.getenv('AGIO_WORKSPACE_SUFFIX') or ''

    def set_suffix(self, suffix: str):
        """Customize pyproject location folder name"""
        self._kwargs['root_suffix'] = suffix
        self._extra_launch_envs['AGIO_WORKSPACE_SUFFIX'] = suffix

    @property
    def custom_py_executable(self) -> str:
        return str(self._kwargs.get('py_executable', ''))

    # creation

    @classmethod
    def from_workspace(cls, workspace: AWorkspace|str, **kwargs) -> 'AWorkspaceManager':
        if isinstance(workspace, str):
            data = api.workspace.get_revision_by_workspace_id(workspace)
            revision = AWorkspaceRevision(data)
            return cls(revision, **kwargs)
        elif isinstance(workspace, AWorkspace):
            current_revision = workspace.get_current_revision()
            return cls(current_revision, **kwargs)

    @property
    def settings_id(self):
        return self._kwargs.get('settings_revision_id')

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

    # define
    @classmethod
    def current(cls) -> 'AWorkspaceManager':
        if ws_id := os.getenv(env_names.WORKSPACE_ENV_NAME):
            return cls.from_workspace(ws_id)
        elif rev_id := os.getenv(env_names.REVISION_ENV_NAME):
            return cls(rev_id)

    @classmethod
    def default(cls):
        return cls(root=app_dirs.default_env_install_dir())

    @classmethod
    def is_defined(cls):
        return bool(os.getenv(env_names.WORKSPACE_ENV_NAME)) or bool(os.getenv(env_names.REVISION_ENV_NAME))

    # props

    def get_workspace(self) -> AWorkspace:
        if not self._revision:
            raise DefaultWorkspaceError('No revision for default workspace')
        return AWorkspace(self.workspace_id)

    @property
    def workspace_id(self):
        if not self._revision:
            raise DefaultWorkspaceError('No ID for default workspace')
        return self.revision.workspace_id

    @property
    def revision(self):
        return self._revision

    @property
    def root(self):
        if self._install_root:
            return self._install_root
        return Path(config.WS.INSTALL_DIR, self.workspace_id).expanduser().resolve()

    @property
    def install_root(self):
        if self._install_root:
            return Path(self._install_root)
        return self.root.joinpath('-'.join([self.revision.id, self.root_suffix]).strip('-'))

    @property
    def bin_path(self):
        return self.install_root / '.venv/bin'

    def get_package_list(self):
        if not self._revision:
            # TODO get package list for default workspace
            raise DefaultWorkspaceError('No package list for default workspace')
        return self.revision.get_package_list()

    def get_py_version(self):
        custom = self._kwargs.get('python_version')
        if custom:
            return custom
        if self.revision:
            return self.revision.metadata.get('py_version', {}).get(sys.platform.lower())
        return self.default_python_version

    # install and manage

    @cached_property
    def venv_manager(self):
        return pkg_manager.get_package_manager(self.install_root, self.custom_py_executable)

    def install(self, clean: bool = False, no_cache: bool = False):

        logger.debug(f'Installing workspace {self.install_root}')
        emit('core.workspace.before_install', {'workspace': self})
        # check package list
        if self.revision:
            package_list = list(self.get_package_list())
        else:
            package_list = []
        # create or recreate venv
        reinstall = clean or self.need_to_reinstall()
        if reinstall:
            logger.info('Reinstalling workspace...')
            if self.is_installed():
                self.remove()
            py_version_required = self.get_py_version()
            self.venv_manager.create_venv(py_version_required)
        # install packages
        if package_list:
            self.install_packages(*package_list, no_cache=no_cache)
        # save meta file
        if self.revision:
            with open(self.local_meta_file, 'w') as f:
                data = copy.deepcopy(self.revision.to_dict())
                data['workspace_suffix'] = self.root_suffix
                json.dump(data, f, indent=4)
            logger.debug(f'meta file saved: {self.local_meta_file}')
            emit('core.workspace.installed',
                    {'revision': self.revision.id,
                     'packages': package_list,
                     'meta_filename': self.local_meta_file,
                     'workspace_manager': self
                     }
                 )
        else:
            emit('core.workspace.installed',
                 {'revision': None,
                  'packages': [],
                  'meta_filename': None,
                  'workspace_manager': self
                  }
                 )
        logger.debug('Installation complete')

    def install_packages(self, *package_list: APackageRelease|str, **kwargs):
        package_list = collect_packages_to_install(package_list)
        install_args = [pkg.get_installation_command() for pkg in package_list]
        # print('-'*100)
        # print('Python version:', self.venv_manager.get_python_version())
        # print('-'*100)
        # for pkg in install_args:
        #     print(pkg)
        # print('-'*100)
        logger.info(f'Packages to install: {len(package_list)}')
        status_code = self.venv_manager.install_packages(*install_args, **kwargs)
        if status_code:
            raise Exception(f'Failed to install packages. Status code:{status_code}')
        # on pacakge installed callbacks
        for pkg in self.iter_installed_packages():
            pkg.execute_package_callback('on_installed', self)

    def uninstall_packages(self, *packages: APackage|APackageRelease|str):
        existing_packages = []
        for p in packages:
            if isinstance(p, APackage):
                existing_packages.append(p)
            elif isinstance(p, APackageRelease):
                existing_packages.append(p.get_package())
            elif isinstance(p, str):
                existing_packages.append(APackage.find(name=p))
            else:
                raise TypeError(f'Unsupported package type: {type(p)}')
        packages = existing_packages
        all_installed = {x.package_name: x for x in list(self.iter_installed_packages())}
        to_uninstall = [man for _, man in all_installed.items() if man.package in packages]
        logger.info(f'Before uninstall callbacks')
        for pkg in to_uninstall:
            pkg.execute_package_callback('before_uninstalling', self)
        install_args = [pkg.name for pkg in packages]
        status_code = self.venv_manager.uninstall_packages(*install_args)
        if status_code:
            raise Exception(f'Failed to install packages. Status code:{status_code}')

    def is_installed(self):
        return self.local_meta_file.exists()

    def need_to_reinstall(self):
        if self.is_installed():
            required_py_version = self.get_py_version()
            if required_py_version:
                current_version = self.venv_manager.get_python_version(full=True)
                if not check_current_python_version(
                        required_py_version,
                        current_version):
                    return True
        # TODO: check module list hash
        else:
            return True

    @cache
    def get_site_packages_path(self):
        if not self.is_installed():
            raise WorkspaceNotInstalled('Workspace revision not installed locally')
        return self.venv_manager.site_packages

    def remove(self, fast=False) -> bool:
        emit('core.workspace.before_remove', {'revision': self, 'fast': fast})
        if self.is_installed():
            if not fast:
                self.uninstall_packages(*self.iter_installed_packages())
            self.venv_manager.delete_venv()
            shutil.rmtree(self.install_root)
            emit('core.workspace.removed', {'revision': self, 'fast': fast})
            return True
        return False

    def touch(self):
        """Update latest time usage"""
        if not self.is_installed():
            raise WorkspaceNotInstalled('Workspace revision not installed locally')
        timestamp_file = self.install_root / 'timestamp'
        if not timestamp_file.exists():
            self.install_root.mkdir(parents=True, exist_ok=True)
            timestamp_file.write_text(
                '--- Uses the access time of this file as the last access time of the workspace ---'
            )
        timestamp_file.touch(exist_ok=True)

    def get_latest_used_datetime(self):
        if not self.is_installed():
            raise WorkspaceNotInstalled('Workspace revision not installed locally')
        timestamp_file = self.install_root / 'timestamp'
        return datetime.fromtimestamp(timestamp_file.stat().st_atime)

    # packages

    def iter_installed_packages(self, *names):
        yield from self.venv_manager.iter_packages(*names)

    # modify and launch

    def set_py_executable(self, py_executable: str):
        if 'venv_manager' in self.__dict__:
            self.__dict__.pop('venv_manager')
        self._kwargs['py_executable'] = py_executable

    def get_pyexecutable(self) -> str:
        self.install_or_update_if_needed()
        return self.venv_manager.python_executable

    def add_launch_envs(self, launch_envs: dict):
        self._extra_launch_envs.update(launch_envs)

    def get_launch_envs(self):
        env = {
            **self._extra_launch_envs,
            env_names.COMPANY_ENV_NAME: self.get_workspace().company_id,
            env_names.WORKSPACE_ENV_NAME: str(self.revision.workspace_id),
            env_names.REVISION_ENV_NAME: str(self.revision.id),
            'VIRTUAL_ENV': self.install_root.as_posix()
        }
        if self.settings_id:
            env[env_names.SETTINGS_REVISION_ENV_NAME] = str(self.settings_id)
        emit('core.workspace.get_launch_envs', {'envs': env, 'revision': self._revision})
        return env

    def get_launch_context(self):
        ctx = LaunchContext(
            self.get_pyexecutable(),
            env=self.get_launch_envs()
        )
        return ctx

    def install_or_update_if_needed(self):
        # TODO
        if not self.is_installed():
            self.install()

    @classmethod # TODO cache it
    def create_from_id(cls, entity_id: str) -> 'AWorkspaceManager':
        # is workspace id
        try:
            revision = api.workspace.get_revision_by_workspace_id(entity_id)
            return cls(revision)
        except NotExistsError:
            pass
        # is workspace name
        # TODO api.workspace.get_revision_by_workspace_label
        # is revision id
        try:
            revision = api.workspace.get_revision(entity_id)
            return cls(revision)
        except NotExistsError:
            pass
        # is settings id
        try:
            revision = api.workspace.get_revision_by_settings_id(entity_id)
            return cls(revision, settings_revision_id=entity_id)
        except NotExistsError:
            pass
        # is project id
        try:
            revision = api.workspace.get_revision_by_project_id(entity_id)
            manager = cls(revision)
            manager.add_launch_envs({'AGIO_PROJECT_ID': entity_id})
            return manager
        except NotExistsError:
            pass
        raise WorkspaceNotExists
