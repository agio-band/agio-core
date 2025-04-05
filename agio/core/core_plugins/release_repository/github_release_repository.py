import os
from pathlib import Path
import logging
import requests
from agio.core.plugins.base.release_repository_base_plugin import ReleaseRepositoryPlugin
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class GitHubRepository(ReleaseRepositoryPlugin):
    name = 'github'
    check_url_pattern = r'https://github\.com.*'

    @classmethod
    def parse_url(cls, url: str):
        parsed = urlparse(url)
        return dict(
            domain=parsed.netloc,
            username=parsed.path.split('/')[1],
            repository_name=parsed.path.split('/')[2],
            repository_path='/'.join(parsed.path.strip('/').split('/')[0:2])
        )

    def download_release_file(self, tag: str, file_type: str = 'whl', dest_dir: str | Path = None) -> str:
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
        url = f"https://api.github.com/repos/{repo_details['username']}/{repo_details['repository_name']}/releases"
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }
        data = {
            "tag_name": tag,
            "name": name,
            "body": notes,
            "draft": False,
            "prerelease": None
        }
        logger.debug(f'Crate release url: {url}')
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        release_data = response.json()
        upload_url = release_data["upload_url"].split("{?")[0]
        if build_dir:
            for filename in os.listdir(build_dir):
                filepath = os.path.join(build_dir, filename)
                if os.path.isfile(filepath):
                    self.upload_github_file(upload_url, filepath)
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