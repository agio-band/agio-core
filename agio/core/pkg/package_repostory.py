import logging
from functools import cached_property
from pathlib import Path

from agio.core.domains import APackageRelease, APackage
from agio.core.exceptions import PackageRepositoryError, PackageError, PackageLoadingError
from agio.core.pkg.package import APackageManager
from agio.core.plugins.base_remote_repository import RemoteRepositoryPlugin
from agio.core.utils import git_utils
from agio.core.utils.pkg_manager import get_package_manager
from agio.core import api
from agio.core.utils import plugin_hub

logger = logging.getLogger(__name__)


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
        if not self.pkg_manager.package:
            raise PackageError(f"Package '{self.pkg_manager.package_name}' not registered")
        # check release version is already exists
        if self.pkg_manager.release:
            raise ValueError(f"Release {self.pkg_manager.package_name} {self.pkg_manager.package_version} "
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
        if self.pkg_manager.package_version in remote_tags:
            if self.remote_repository.get_release_with_tag(self.pkg_manager.source_url, self.pkg_manager.package_version, access_data):
                raise ValueError(f"Version {self.pkg_manager.package_name} already exists in remote repository")
        # build
        build_path = self.build(**kwargs)
        # create release on remote repository
        self.remote_repository.create_and_upload_release(
            self.pkg_manager.source_url,
            self.pkg_manager.package_version,
            build_path,
        )
        release = self.remote_repository.get_release_with_tag(
            self.pkg_manager.source_url,
            self.pkg_manager.package_version,
            access_data)
        if not release:
            raise Exception(
                f"Release {self.pkg_manager.package_name} {self.pkg_manager.package_version} not found in repository"
            )
        if not release.get('assets'):
            raise Exception(f"Release {self.pkg_manager.package_version} has no assets")
        assets = []
        for ast in release['assets']:
            assets.append(dict(
                name=ast['name'],
                size=ast['size'],
                url=ast['browser_download_url'],
            ))
        self.register_release(assets, metadata=self.pkg_manager.get_pacakge_metadata())
        release_data = dict(
            release_url=release['html_url'],
            assets=assets,
            version=self.pkg_manager.package_version,
            release_id=release['id'],
            created_at=release['created_at'],
        )
        return release_data

    @cached_property
    def py_package_manager(self):
        return get_package_manager(self.root)

    def build(self, **kwargs):
        return self.py_package_manager.build_package(**kwargs)

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

    def remove_release(self):
        pass

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
        raise PackageLoadingError('No repo url provided')
    for plugin in plugin_hub.APluginHub.instance().get_plugins_by_type('remote_repository'):
        if repository_api and repository_api == plugin.repository_api:
            return plugin
        if plugin.check_is_valid_url(repo_url):
            return plugin
    raise PackageLoadingError(f'No Release repository plugin found for url: {repo_url}. '
                              f'Use meta variable "repository_api" in __agio__.yml file '
                              f'to specify the repository API manually.')
