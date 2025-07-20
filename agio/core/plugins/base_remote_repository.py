import logging
import re
from fnmatch import fnmatch
from pathlib import Path

from agio.core.plugins.mixins import BasePluginClass
from agio.core.plugins.base_plugin import APlugin

logger = logging.getLogger(__name__)


class RemoteRepositoryPlugin(BasePluginClass, APlugin):
    plugin_type = 'remote_repository'
    _default_file_ignore_list = ['.*', '__pycache__']
    check_url_pattern = None
    access_token_env = None
    access_token_field_name = 'token'
    file_ignore_list = []

    @property
    def ignore_list(self):
        return self._default_file_ignore_list + self.file_ignore_list

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
        Create new release and upload files to remote storage, return release url
        """
        raise NotImplementedError

    def delete_release(self, repository_url: str, tag: str, access_data: dict = None):
        raise NotImplementedError

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
        Get release asset list
        """
        raise NotImplementedError

    def get_asset_list(self, repository_url: str, tag: str, access_data: dict) -> list:
        raise NotImplementedError

    def validate_file_name_with_ignore_list(self, filename: str, ignore_list: list = ()):
        if not ignore_list:
            return True
        for pattern in ignore_list:
            if fnmatch(filename, pattern):
                return False
        return True

    @classmethod
    def check_is_valid_url(cls, url: str):
        if not cls.check_url_pattern:
            return False
        return bool(re.match(cls.check_url_pattern, url))

