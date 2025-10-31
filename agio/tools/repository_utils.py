import logging
import re
from pathlib import Path
from typing import List
from urllib.parse import urlparse

import requests
from packaging.tags import sys_tags, Tag
from packaging.utils import parse_wheel_filename

logger = logging.getLogger(__name__)


def extract_repo_info(repo_url: str):
    match = re.match(r"https?://([^/]+)/(?:([^/]+)/)*([^/]+)", repo_url)
    if not match:
        raise ValueError("Invalid repository URL")
    domain, repo_path, repo_name = match.groups()
    if "github.com" in domain:
        platform = "github"
    elif "gitlab" in domain:
        platform = "gitlab"
    else:
        raise ValueError("Unsupported platform")
    return platform, domain, (repo_path.strip('/') if repo_path else '') + '/' + repo_name


def get_github_whl_url(repo_url: str, package_version: str):
    platform, domain, repo_path = extract_repo_info(repo_url)
    releases_url = f"https://{domain}/repos/{repo_path}/releases/tags/{package_version}"
    return fetch_whl_url(releases_url)


def get_gitlab_whl_url(repo_url: str, package_version: str):
    platform, domain, repo_path = extract_repo_info(repo_url)
    releases_url = f"https://{domain}/api/v4/projects/{requests.utils.requote_uri(repo_path)}/releases/{package_version}"
    return fetch_whl_url(releases_url)


def fetch_whl_url(releases_url: str):
    compatible_tags = list(sys_tags())
    response = requests.get(releases_url)
    response.raise_for_status()
    assets = response.json().get("assets", {})
    links = assets.get("links", [])

    for asset in assets:
        if not asset["name"].endswith(".whl"):
            continue
        try:
            name, version, build, tags_whl = parse_wheel_filename(asset["name"])
            if any(tag in tags_whl for tag in compatible_tags):
                return asset["url"]
        except Exception as e:
            print(f"Warning: unexpected error parsing wheel '{asset['name']}': {e}")
            continue
    raise ValueError("No compatible .whl found for your platform.")


def get_compatible_whl_url(repo_url: str, package_version: str):
    platform, _, _ = extract_repo_info(repo_url)
    if platform == "github":
        return get_github_whl_url(repo_url, package_version)
    elif platform == "gitlab":
        return get_gitlab_whl_url(repo_url, package_version)
    else:
        raise ValueError("Unsupported platform")


def filter_compatible_package(files: List[str]) -> str:
    compatible_tags = list(sys_tags())

    def score_wheel(tags_whl: List[Tag]) -> int:
        return sum(
            (len(compatible_tags) - compatible_tags.index(tag))
            for tag in tags_whl if tag in compatible_tags
        )

    best_match = None
    best_score = -1

    for file in files:
        short = Path(file).name
        try:
            _, _, _, tags_whl = parse_wheel_filename(short)
            score = score_wheel(tags_whl)
            if score > best_score:
                best_score = score
                best_match = file
        except Exception as e:
            print(f"Warning: unexpected error parsing wheel '{file}': {e}")
            continue

    if best_match:
        return best_match
    raise ValueError("No compatible .whl found for your platform. Probably incorrect file name?")



class GitUrl:
    def __init__(self, url: str, token: str = None, secure_http: bool = False):
        self.original_url = url
        self.token = token
        self.secure_http = secure_http
        self.parts = self._parse_url(url)

    def __repr__(self):
        return f"<GitUrl(original='{self.original_url}')>"

    def _parse_url(self, url: str):
        # SCP-like SSH format: git@github.com:user/repo.git (без схемы!)
        if not re.match(r'^\w+://', url):  # Нет схемы — это SCP
            scp_like = re.match(r'^(?P<user>[^@]+)@(?P<host>[^:]+):(?P<path>.+)$', url)
            if scp_like:
                return {
                    'scheme': 'ssh',
                    'user': scp_like.group('user'),
                    'host': scp_like.group('host'),
                    'path': scp_like.group('path'),
                    'port': None
                }

        # url with schema
        parsed = urlparse(url)
        return {
            'scheme': parsed.scheme,
            'user': parsed.username or '',
            'host': parsed.hostname,
            'path': parsed.path.lstrip('/'),
            'port': parsed.port
        }

    @property
    def http(self):
        if self.secure_http or self.parts['scheme'] == 'https':
            scheme = 'https'
        else:
            scheme = 'http'
        user = self.parts['user'] or 'git'
        host = self.parts['host']
        path = self.parts['path']
        if self.token:
            return f"{scheme}://{user}:{self.token}@{host}/{path}"
        return f"{scheme}://{host}/{path}"

    @property
    def ssh(self):
        """Convert to SSH URL: git@host:user/repo.git"""
        user = self.parts['user'] or 'git'
        host = self.parts['host']
        path = self.parts['path']
        return f"{user}@{host}:{path}"

    def to_ssh_url_scheme(self):
        """Convert to ssh://git@host[:port]/user/repo.git (not SCP-like)"""
        user = self.parts['user'] or 'git'
        host = self.parts['host']
        path = self.parts['path']
        port = f":{self.parts['port']}" if self.parts['port'] else ""
        return f"ssh://{user}@{host}{port}/{path}"


