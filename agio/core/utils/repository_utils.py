from pathlib import Path
from typing import List

import requests
import re
from packaging.tags import sys_tags, Tag
from packaging.utils import parse_wheel_filename
from requests.exceptions import RequestException


# def get_compatible_whl_url(repo_owner: str, repo_name: str, package_version: str):
#     compatible_tags = list(sys_tags())
#     releases_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/releases/{package_version}"
#
#     try:
#         response = requests.get(releases_url)
#         response.raise_for_status()
#         assets = response.json().get("assets", [])
#     except RequestException as e:
#         raise RuntimeError(f"Failed to fetch GitHub release: {e}")
#
#     for asset in assets:
#         if not asset["name"].endswith(".whl"):
#             continue
#         try:
#             name, version, build, tags_whl = parse_wheel_filename(asset["name"])
#             if any(tag in tags_whl for tag in compatible_tags):
#                 return asset["browser_download_url"]
#         except InvalidWheelFilename:
#             continue
#         except Exception as e:
#             print(f"Warning: unexpected error parsing wheel '{asset['name']}': {e}")
#             continue
#     raise ValueError("No compatible .whl found for your platform.")


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
    raise ValueError("No compatible .whl found for your platform.")
