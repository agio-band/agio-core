import logging
import os
import platform
import stat
from pathlib import Path

import requests

from agio.core.workspaces import AWorkspaceManager, APackageManager
from agio.tools import network as net, app_dirs

logger = logging.getLogger(__name__)

EXT = '.exe' if os.name == 'nt' else ''
DOWNLOAD_URL = f'https://storage.yandexcloud.net/agio-public/login/latest/{platform.system().lower()}/amd64/bin/agio-login{EXT}'


def on_installed(package: APackageManager, ws_manager: AWorkspaceManager):
    binary = download_to_global()
    # make executable
    if os.name != 'nt':
        file = Path(binary)
        mode = file.stat().st_mode
        file.chmod(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def download_to_global():
    save_path = app_dirs.binary_files_dir()
    if check_is_need_to_download(save_path):
        path = download_binary(save_path)
        save_local_etag(get_remote_etag())
        return path
    else:
        logger.info(f'Skipping download of agio-login, already exists')
        return find_local_file(save_path)


def check_is_need_to_download(path: Path) -> bool:
    if find_local_file(path):
        remote_etag = get_remote_etag()
        local_etag = get_local_etag()
        if remote_etag == local_etag:
            return False
    return True


def download_binary(destination_path: Path) -> str:
    logger.info(f'Download url: {DOWNLOAD_URL} to {destination_path}')
    return net.download_file(DOWNLOAD_URL, str(destination_path), allow_redirects=True, skip_exists=False)


def get_remote_etag():
    try:
        with requests.get(DOWNLOAD_URL, stream=True) as response:
            response.raise_for_status()
            return response.headers.get('ETag')
    except requests.exceptions.RequestException as e:
        raise Exception(f'Failed to get ETag from {DOWNLOAD_URL}') from e


def find_local_file(path: Path):
    return next(path.glob('agio-login*'), None)


def get_local_etag():
    file = app_dirs.cache_dir('agio-login-etag')
    if file.exists():
        return file.read_text()


def save_local_etag(etag: str):
    file = app_dirs.cache_dir('agio-login-etag')
    file.parent.mkdir(parents=True, exist_ok=True)
    file.touch()
    file.write_text(etag)

