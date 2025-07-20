import os
import re
import time
from pathlib import Path
import logging
import requests

from agio.core.exceptions import MakeReleaseError
from agio.core.plugins.base_remote_repository import RemoteRepositoryPlugin
from urllib.parse import urlparse

from agio.core.utils import config

logger = logging.getLogger(__name__)


class GitHubRepositoryPlugin(RemoteRepositoryPlugin):
    name = 'github_repository'
    repository_api = 'github'
    check_url_pattern = r'https://github\.com.+'
    default_token = os.getenv('GITHUB_TOKEN')

    def get_token(self, access_data: dict) -> str:
        token = self.default_token
        if access_data:
            token = access_data.get('token', None)
        if not token:
            raise Exception("No token provided")
        return token

    def get_headers(self, access_data, extra_headers: dict = None):
        return {
            'Accept': 'application/vnd.github.v3+json',
            'Accept-Charset': 'application/vnd.github.v3+json',
            'Authorization': f'Bearer {self.get_token(access_data)}',
            **(extra_headers or {})
        }

    @classmethod
    def parse_url(cls, url: str):
        parsed = urlparse(url)
        username, repo_name = parsed.path.strip('/').split('/')
        return dict(
            schema=parsed.scheme,
            domain=parsed.netloc,
            username=username,
            repository_name=repo_name,
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

        asset_files = []
        build_dir = Path(build_dir)
        if not build_dir.is_dir():
            raise MakeReleaseError(f"Build directory {build_dir} does not exist")

        ignore_list = self.ignore_list + list((ignore_list or []))

        for filepath in build_dir.iterdir():
            filepath: Path
            if filepath.is_file():
                rel_path = filepath.relative_to(build_dir).as_posix()
                if not self.validate_file_name_with_ignore_list(rel_path, ignore_list):
                    logger.debug(f"File {rel_path} is ignored")
                    continue
                asset_files.append(filepath)

        repo_details = self.parse_url(repository_url)
        # TODO: check release already exists
        base_url = self.get_api_base_url(repository_url)
        repo_name = re.sub(r"\.git$", '', repo_details['repository_name'])
        url = f"{base_url}/repos/{repo_details['username']}/{repo_name}/releases"
        headers = self.get_headers(access_data)
        data = {
            "tag_name": tag,
            "name": name or tag,
            "body": notes or '',
            "draft": False,
            "prerelease": False
        }
        logger.info(f'Crate release url: {url}')
        # create release
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        release_data = response.json()
        upload_url = release_data["upload_url"].split("{?")[0]
        # upload files
        for file_path in asset_files:
            logger.info(f"Upload file {file_path}")
            self.upload_github_file(upload_url, file_path.as_posix(), access_data)
        assets_url = release_data['assets_url']
        resp = requests.get(assets_url, headers=headers)
        resp.raise_for_status()
        # assets = []
        # for ast in resp.json():
        #     assets.append({
        #         'url': ast['browser_download_url'],
        #     })
        return release_data

    def upload_github_file(self, upload_url: str, filepath: str, access_data: dict = None):
        filename = os.path.basename(filepath)
        headers = {
            **self.get_headers(access_data),
            "Content-Type": "application/octet-stream"
        }
        with open(filepath, "rb") as file:
            response = requests.post(f"{upload_url}?name={filename}", headers=headers, data=file.read())
        if response.status_code == 201:
            logger.info(f"File {filename} uploaded successfully to GitHub")
        else:
            raise MakeReleaseError(response.text)

    def get_api_base_url(self, repository_url: str):
        repo_details = self.parse_url(repository_url)
        return "{schema}://api.{domain}".format(**repo_details)

    def get_release_with_tag(self, repository_url: str, tag: str, access_data: dict) -> dict | None:
        base_url = self.get_api_base_url(repository_url)
        repo_details = self.parse_url(repository_url)
        url = f'{base_url}/repos/{repo_details['username']}/{repo_details['repository_name']}/releases/tags/{tag}'
        headers = self.get_headers(access_data)

        logger.debug(f"Checking if release exists: {url}")
        retry = 0
        while retry < config.API.MAX_REQUEST_ATTEMPTS:
            response = requests.get(url, headers=headers)
            if response.ok:
                return response.json()
            elif response.status_code == 404:
                retry += 1
                logger.info(f"Error on request {response.reason}")
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

    def delete_release(self, repository_url: str, tag: str, access_data: dict) -> dict | None:
        headers = self.get_headers(access_data)
        base_url = self.get_api_base_url(repository_url)
        repo_details = self.parse_url(repository_url)
        releases_url = f'{base_url}/repos/{repo_details['username']}/{repo_details['repository_name']}/releases'
        response = requests.get(releases_url, headers=headers)
        if not response.ok:
            raise Exception(response.text)

        releases = response.json()
        release_id = None

        for release in releases:
            if release['tag_name'] == tag:
                release_id = release['id']
                break

        if not release_id:
            logger.warning(f"No release found for tag {tag}")
            return

        delete_url = f'{base_url}/repos/{repo_details['username']}/{repo_details['repository_name']}/releases/{release_id}'
        delete_resp = requests.delete(delete_url, headers=headers)

        if delete_resp.status_code == 204:
            logger.info(f"Release {tag} successfully deleted")
        else:
            logger.error(delete_resp.text)


        ref_url = f'{base_url}/repos/{repo_details['username']}/{repo_details['repository_name']}/git/refs/tags/{tag}'
        ref_resp = requests.delete(ref_url, headers=headers)

        if ref_resp.status_code == 204:
            logger.info(f"Release {tag} successfully deleted")
        else:
            logger.error(ref_resp.text)