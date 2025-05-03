import os
import re
import time
from pathlib import Path
import logging
import requests
from agio.core.plugins.base.base_plugin_release_repository import ReleaseRepositoryPlugin
from urllib.parse import urlparse
from fnmatch import fnmatch

logger = logging.getLogger(__name__)


class GitHubRepositoryPlugin(ReleaseRepositoryPlugin):
    repository_api = 'github'
    check_url_pattern = r'https://github\.com.*'

    @classmethod
    def parse_url(cls, url: str):
        parsed = urlparse(url)
        return dict(
            schema=parsed.scheme,
            domain=parsed.netloc,
            username=parsed.path.split('/')[1],
            repository_name=parsed.path.split('/')[2],
            repository_path='/'.join(parsed.path.strip('/').split('/')[0:2])
        )

    @classmethod
    def download_package_release(
            cls,
            repository_url: str,
            tag: str,
            file_type: str = 'whl',
            dest_dir: str | Path = None
    ) -> str:
        # TODO
        pass

    def create_and_upload_release(
            self,
            repository_url: str,
            tag: str,
            build_dir: str | Path,
            access_data: dict = None,
            name: str = None,
            notes: str = None,
            ignore_list: list = None
        ) -> str:
        repo_details = self.parse_url(repository_url)
        token = access_data.get('token', None)
        if not token:
            raise Exception("No token provided")
        # TODO: check release already exists
        base_url = self.get_api_base_url(repository_url)
        repo_name = re.sub(r"\.git$", '', repo_details['repository_name'])
        url = f"{base_url}/repos/{repo_details['username']}/{repo_name}/releases"
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }
        data = {
            "tag_name": tag,
            "name": name or tag,
            "body": notes or '',
            "draft": False,
            "prerelease": False
        }
        logger.info(f'Crate release url: {url}')
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        release_data = response.json()
        upload_url = release_data["upload_url"].split("{?")[0]
        ignore_list = self.release_ignore_list + list((ignore_list or []))
        if build_dir:
            for filename in os.listdir(build_dir):
                filepath = os.path.join(build_dir, filename)
                if os.path.isfile(filepath):
                    rel_path = os.path.relpath(filepath, build_dir)
                    if not self.validate_file_name_with_ignore_list(rel_path, ignore_list):
                        logger.debug(f"File {rel_path} is ignored")
                        continue
                    self.upload_github_file(upload_url, filepath, access_data)
        return release_data

    def upload_github_file(self, upload_url: str, filepath: str, access_data: dict = None):
        token = access_data.get('token', None)
        if not token:
            raise Exception("No token provided")
        filename = os.path.basename(filepath)
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/octet-stream"
        }
        with open(filepath, "rb") as file:
            response = requests.post(f"{upload_url}?name={filename}", headers=headers, data=file.read())
        if response.status_code == 201:
            logger.info(f"File {filename} uploaded successfully to GitHub")
        else:
            raise Exception(response.text)

    def get_api_base_url(self, repository_url: str):
        repo_details = self.parse_url(repository_url)
        return "{schema}://{domain}".format(**repo_details)

    def get_release_with_tag(self, repository_url: str, tag: str, access_data: dict) -> dict | None:
        token = access_data.get('token', None)
        if not token:
            raise Exception("No token provided")

        base_url = self.get_api_base_url(repository_url)
        repo_details = self.parse_url(repository_url)
        url = f'{base_url}/repos/{repo_details['username']}/{repo_details['repository_name']}/releases/tags/{tag}'
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }

        logger.debug(f"Checking if release exists: {url}")
        retry = 0
        while retry < 3:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                retry += 1
                logger.info('Retry...')
                time.sleep(.5)
                continue
            else:
                logger.warning(f"GitHub API error: {response.status_code} {response.text}")
                response.raise_for_status()

    def get_asset_list(self, repository_url: str, tag: str, access_data: dict) -> list:
        release_data = self.get_release_with_tag(repository_url, tag, access_data)
        if not release_data:
            return []
        return release_data['assets']