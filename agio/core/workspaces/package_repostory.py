import logging
import shutil
import tempfile
from functools import cached_property
from pathlib import Path

import yaml

from agio.core import api
from agio.core.entities import APackageRelease, APackage
from agio.core.exceptions import PackageRepositoryError, PackageError, PackageLoadingError
from agio.core.plugins import plugin_hub
from agio.core.plugins.base_remote_repository import RemoteRepositoryPlugin
from agio.core.workspaces.package import APackageManager
from agio.core.workspaces import workspace
from agio.tools import git_utils, file_utils
from agio.tools.pkg_manager import get_package_manager

logger = logging.getLogger(__name__)


class APackageRepository:
    """
    Manage package repository
    """
    def __init__(self, repository_root: str|Path):
        self.root = Path(repository_root)
        self.check_repository_root()

    def repository_is_valid(self):
        return self.root.is_dir() and self.root.joinpath('pyproject.toml').exists()

    def check_repository_root(self):
        if not self.repository_is_valid():
            raise PackageRepositoryError(f"Repository '{self.root}' is not valid. File pyproject.toml not found")

    @cached_property
    def pkg_manager(self):
        return APackageManager.find_package(self.root)

    @cached_property
    def remote_repository(self) -> RemoteRepositoryPlugin:
        return get_remote_repository_plugin(self.pkg_manager.source_url, self.pkg_manager.repository_api)

    @property
    def origin(self):
        return git_utils.get_remote_url(self.root.as_posix())

    def make_release(self, **kwargs):
        """
        Make and register a new release from current version.
        """
        # check package registered
        logger.debug(f"Creating new release...")
        logger.debug(f"Check package is registered")
        if not self.pkg_manager.package:
            raise PackageError(f"Package '{self.pkg_manager.package_name}' not registered")
        # check unsaved changes
        if not kwargs.get('no_check_branch', False):
            logger.debug(f"Checking git branch...")
            active_branch = git_utils.get_current_branch(self.root.as_posix())
            if active_branch not in ('main', 'master'):
                raise ValueError(f"Branch is not main or master ({active_branch})")
        else:
            logger.debug('Skip branch check')
        # check uncommited changes
        if not kwargs.get('no_check_commits', False):
            logger.debug(f"Checking uncommited changes...")
            if git_utils.has_uncommited_changes(self.root.as_posix()):
                raise ValueError(f"Has uncommited changes")
        else:
            logger.debug('Skip uncommited changes check')
        # check unpushed commits
        if not kwargs.get('no_check_pushed', False):
            logger.debug(f"Checking unpushed changes...")
            if git_utils.has_unpushed_commits(self.root.as_posix()):
                raise ValueError(f"Has unpushed commits")
        else:
            logger.debug('Skip unpushed changes check')
        # check release version is already exists in agio database
        replace = kwargs.pop('replace', False)
        if self.pkg_manager.release:
            if not replace:
                raise ValueError(f"Release {self.pkg_manager.package_name} v{self.pkg_manager.package_version} "
                                 f"already registered in agio database")
        access_data = kwargs.get('access_data', {})
        if 'token' in kwargs:
            access_data['token'] = kwargs.pop('token')
            if not access_data['token']:
                raise ValueError(f"Access token is required")
            logger.debug(f"Use token: {access_data['token'][:5]}...")
        # check version is not exists in remote
        local_tags, remote_tags = git_utils.get_tags(self.root.as_posix(), self.origin)
        release = None
        if self.pkg_manager.package_version in remote_tags:
            if release := self.remote_repository.get_release_with_tag(
                    self.pkg_manager.source_url,
                    self.pkg_manager.package_version,
                    access_data):
                if replace:
                    logger.info(f'Delete release {self.pkg_manager.package_name}')
                    self.remote_repository.delete_release(
                        self.pkg_manager.source_url,
                        self.pkg_manager.package_version,
                        access_data
                    )
                else:
                    raise ValueError(f"Version {self.pkg_manager.package_name} already exists in remote repository")
        # build
        logger.debug(f'Build release...')
        build_path = self.build(**kwargs)
        # create local tag
        keep_tag = kwargs.get('keep_tag', False)
        if self.pkg_manager.package_version in local_tags:
            if not keep_tag:
                # move tag to current commit
                git_utils.delete_tag(self.root.as_posix(), self.pkg_manager.package_version)
                git_utils.create_tag(self.root.as_posix(), self.pkg_manager.package_version)
        else:
            git_utils.create_tag(self.root.as_posix(), self.pkg_manager.package_version)
        # create release on remote repository
        logger.debug(f"Upload release...")
        self.remote_repository.create_and_upload_release(
            self.pkg_manager.source_url,
            self.pkg_manager.package_version,
            build_path,
            access_data=access_data,
        )
        # try to get new release
        release = release or self.remote_repository.get_release_with_tag(
            self.pkg_manager.source_url,
            self.pkg_manager.package_version,
            access_data)
        if not release:
            raise Exception(
                f"Release {self.pkg_manager.package_name} {self.pkg_manager.package_version} not found in repository"
            )
        logger.debug(f"Release created!")
        if not release.get('assets'):
            raise Exception(f"Release {self.pkg_manager.package_version} has no assets")
        assets = self.release_to_assets(release)
        self.register_release(assets, metadata=self.pkg_manager.get_pacakge_metadata())
        release_data = dict(
            release_url=release['html_url'],
            assets=assets,
            version=self.pkg_manager.package_version,
            release_id=release['id'],
            created_at=release['created_at'],
        )
        return release_data

    @classmethod
    def release_to_assets(cls, release: dict) -> list:
        assets = []
        for ast in release['assets']:
            assets.append(dict(
                name=ast['name'],
                size=ast['size'],
                url=ast['browser_download_url'],
            ))
        return assets

    @cached_property
    def py_package_manager(self):
        return get_package_manager(self.root)

    def get_package_manager(self) -> APackageManager:
        return APackageManager.find_package(self.root)

    def build(self, **kwargs):
        with tempfile.TemporaryDirectory() as tmpdir:
            file_utils.copy_tree_with_ignore_file(self.root.as_posix(), tmpdir)
            pkg = APackageRepository(tmpdir)
            # update info file
            pkg_manager = pkg.get_package_manager()
            with open(pkg_manager.metadata_file, 'w') as f:
                yaml.dump(pkg_manager.get_pacakge_metadata(), f, default_flow_style=False)
            # start build
            dist = Path(pkg.py_package_manager.build_package(
                python_version=workspace.AWorkspaceManager.default_python_version,
                **kwargs))
            local_dist = self.root/dist.name
            if local_dist.exists():
                shutil.rmtree(local_dist)
            shutil.copytree(dist, local_dist)
            logger.debug(f"Built to: {local_dist}")
        return local_dist

    def register_release(self, assets: list, metadata: dict = None):
        release = APackageRelease.create(
            package_id=self.pkg_manager.package.id,
            version=self.pkg_manager.package_version,
            label=self.pkg_manager.label,
            description=self.pkg_manager.description,
            assets={"whl": assets},
            metadata=metadata,
            # icon
        )
        return release

    def register_package(self, **kwargs):
        pkg_meta_data = self.pkg_manager.get_pacakge_metadata()
        # TODO: check meta data
        # TODO: check repository files
        pkg_name = pkg_meta_data.get('name')
        if not pkg_name:
            raise PackageError(f"Package name not set")
        pkg_api = api.package.create_package(pkg_name)
        return APackage(pkg_api)


def get_remote_repository_plugin(repo_url: str, repository_api: str = None):
    if not repo_url:
        raise PackageLoadingError('No repo url provided. Add field "source_url" to __agio__.yml')
    for plugin in plugin_hub.APluginHub.instance().get_plugins_by_type('remote_repository'):
        if repository_api and repository_api == plugin.repository_api:
            return plugin
        if plugin.check_is_valid_url(repo_url):
            return plugin
    raise PackageLoadingError(f'No Release repository plugin found for url: {repo_url}. '
                              f'Use meta variable "repository_api" in __agio__.yml file '
                              f'to specify the repository API manually.')
