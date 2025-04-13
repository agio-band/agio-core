import os
import re
import logging
from pathlib import Path
from fnmatch import fnmatch

from agio.core.packages.package import APackage, APackageRepository
from agio.core.plugins.mixins import BasePluginClass
from agio.core.plugins.plugin_base import APlugin
from agio.core.utils import git_utils

logger = logging.getLogger(__name__)


class ReleaseRepositoryPlugin(BasePluginClass, APlugin):
    plugin_type = 'release_repository'
    name = None
    check_url_pattern = None
    default_ignore_list = ['.*', '__pycache__']
    access_token_env = None
    access_token_field_name = 'token'
    ignore_list = []

    def __init__(self, package: APackage):
        super().__init__(package)
        self.release_ignore_list = self.default_ignore_list + self.ignore_list

    @classmethod
    def parse_url(cls, url: str):
        """
        Parse url and return dict with parsed data
        """
        raise NotImplementedError

    # create release
    def make_release(
            self,
            package: APackageRepository,
            access_data: dict = None,
            name: str = None,
            note: str = None,
            ignore_list: list = None,
            **kwargs
        ) -> dict:
        """
        Build new release, upload and return release url
        """
        # if not self.check_is_valid_url(package.source_url):
        #     raise ValueError(f"Invalid repository url: {package.source_url}")
        if not access_data:
            if self.access_token_env in os.environ:
                token = os.environ.get(self.access_token_env)
                if token:
                    access_data = {self.access_token_field_name: token}
        access_data = access_data or {}
        if not access_data:
            logger.debug(f'Empty access data for {package.source_url}')
        # check branch (main or master)
        if not kwargs.get('no_check_branch', False):
            active_branch = git_utils.get_current_branch(package.root)
            if active_branch not in ('main', 'master'):
                raise ValueError(f"Branch is not main or master ({active_branch})")
        else:
            logger.debug('Skip branch check')
        # check uncommited changes
        if not kwargs.get('no_check_commits', False):
            if git_utils.has_uncommited_changes(package.root):
                raise ValueError(f"Has uncommited changes")
        else:
            logger.debug('Skip uncommited changes check')
        # check unpushed commits
        if not kwargs.get('no_check_pushed', False):
            if git_utils.has_unpushed_commits(package.root):
                raise ValueError(f"Has unpushed commits")
        else:
            logger.debug('Skip unpushed commits check')
        # check version is not exists in remote
        local_tags, remote_tags = git_utils.get_tags(package.root)
        if package.version in remote_tags:
            if self.get_release_with_tag(package.source_url, package.version, access_data):
                raise ValueError(f"Version {package.version} already exists in remote repository")
        # build release
        from agio.core.packages.package_tools import build_package

        release_dir = build_package(package.root)
        # create and push local tag
        if package.version not in local_tags:
            git_utils.create_tag(package.root, package.version)
        # create and upload release
        self.create_and_upload_release(
            package.source_url,
            package.version,
            release_dir,
            access_data,
            name,
            note,
            ignore_list
        )
        # register release in backend
        release = self.get_release_with_tag(package.source_url, package.version, access_data)
        assets = []
        for ast in release['assets']:
            assets.append(dict(
                name=ast['name'],
                size=ast['size'],
                url=ast['browser_download_url'],
            ))
        release_data = dict(
            release_url=release['html_url'],
            assets=assets,
            version=package.version,
            release_id=release['id'],
            created_at=release['created_at'],
        )
        return release_data

    def create_and_upload_release(
            self,
            repository_url: str,
            tag: str,
            build_dir: str | Path,
            access_data: dict = None,
            name: str = None,
            note: str = None,
            ignore_list: list = None
    ):
        """
        Create new release and return release url
        """
        raise NotImplementedError

    def validate_file_name_with_ignore_list(self, filename: str, ignore_list: list = None):
        for pattern in ignore_list:
            if fnmatch(filename, pattern):
                return False
        return True

    # download release
    def download_package_release(
            self,
            package_name: str,
            tag: str,
            file_type: str = 'whl',
            dest_dir: str | Path = None) -> str:
        """
        Download release and return path to downloaded file
        """
        raise NotImplementedError

    def get_release_with_tag(self, repository_url: str, tag: str, access_data: dict) -> dict | None:
        """
        Check if release with tag exists
        """
        raise NotImplementedError

    def get_asset_list(self, repository_url: str, tag: str, access_data: dict) -> list:
        raise NotImplementedError

    @classmethod
    def check_is_valid_url(cls, url: str):
        if not cls.check_url_pattern:
            raise NotImplementedError
        return bool(re.match(cls.check_url_pattern, url))
