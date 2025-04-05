import os
import re
from pathlib import Path
import logging
from agio.core.packages.package import APackage
from agio.core.plugins.mixins import BasePluginClass
from agio.core.plugins.plugin_base import APlugin
from agio.core.utils import git_tools
from fnmatch import fnmatch

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

    def make_release(
            self,
            package: APackage,
            access_data: dict = None,
            name: str = None,
            note: str = None,
            ignore_list: list = None
        ) -> str:
        """
        Build new release, upload and return release url
        """
        if not self.check_is_valid_url(package.repository_url):
            raise ValueError(f"Invalid repository url: {package.repository_url}")
        if not access_data:
            if self.access_token_env in os.environ:
                token = os.environ.get(self.access_token_env)
                if token:
                    access_data = {self.access_token_field_name: token}
        access_data = access_data or {}
        if not access_data:
            logger.debug(f'Empty access data for {package.repository_url}')
        # check branch (main or master)
        active_branch = git_tools.get_current_branch(package.root)
        if active_branch not in ('main', 'master'):
            raise ValueError(f"Branch is not main or master ({active_branch})")
        # check uncommited changes
        if git_tools.has_uncommited_changes(package.root):
            raise ValueError(f"Has uncommited changes")
        # check unpushed commits
        if git_tools.has_unpushed_commits(package.root):
            raise ValueError(f"Has unpushed commits")
        # check version is not exists in remote
        local_tags, remote_tags = git_tools.get_tags(package.root)
        # pkg = APackage(package_repository_dir)
        if package.version in remote_tags:
            if self.has_release_with_tag(package.repository_url, package.version, access_data):
                raise ValueError(f"Version {package.version} already exists in remote repository")
        # build release
        from agio.core.packages.package_tools import build_package

        release_dir = build_package(package.root)
        # create and push local tag
        if package.version not in local_tags:
            git_tools.create_tag(package.root, package.version)
        # create and upload release
        return self.create_and_upload_release(
            package.repository_url,
            package.version,
            release_dir,
            access_data,
            name,
            note,
            ignore_list
        )

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

    def download_release_file(self, tag: str, file_type: str = 'whl', dest_dir: str | Path = None) -> str:
        """
        Download release and return path to downloaded file
        """
        raise NotImplementedError

    def has_release_with_tag(self, repository_url: str, tag: str, access_data: dict) -> bool:
        """
        Check if release with tag exists
        """
        raise NotImplementedError

    @classmethod
    def check_is_valid_url(cls, url: str):
        if not cls.check_url_pattern:
            raise NotImplementedError
        return bool(re.match(cls.check_url_pattern, url))
