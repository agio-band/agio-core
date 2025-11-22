import os
import tempfile
import time
from typing import Optional, Callable, Any

import requests
from .app_dirs import cache_dir
from .file_utils import unpack_archive
import socket
import logging

logger = logging.getLogger(__name__)

# def download_file(url: str, dest_dir: str, filename: str = None, params: dict = None,
#                   headers=None, allow_redirects=False,
#                   skip_exists: bool = False,
#                   ) -> str:
#     """
#     Скачивает файл по URL и сохраняет в указанную директорию.
#     """
#     filename = filename or url.split("/")[-1]
#     file_path = os.path.join(dest_dir, filename)
#     if skip_exists and os.path.exists(file_path):
#         return file_path
#     os.makedirs(dest_dir, exist_ok=True)
#
#     with requests.get(url, stream=True, params=params, headers=headers, allow_redirects=allow_redirects) as response:
#         response.raise_for_status()
#         with open(file_path, "wb") as f:
#             for chunk in response.iter_content(chunk_size=8192):
#                 f.write(chunk)
#
#     return file_path

def download_file(
        url: str,
        dest_dir: str,
        filename: str = None,
        params: dict[str, Any] = None,
        headers: dict[str, str] = None,
        allow_redirects: bool = False,
        skip_exists: bool = False,
        callback: Optional[Callable[[dict[str, Any]], None]] = None,
) -> str:
    filename = filename or url.split("/")[-1]
    file_path = os.path.join(dest_dir, filename)
    callback = callback or simple_progress_callback

    if skip_exists and os.path.exists(file_path):
        if callback:
            callback({"status": "skipped", "file_path": file_path})
        return file_path

    os.makedirs(dest_dir, exist_ok=True)
    start_time = time.time()

    with requests.get(url, stream=True, params=params, headers=headers, allow_redirects=allow_redirects) as response:
        response.raise_for_status()
        total_size_str = response.headers.get('content-length')
        total_size = int(total_size_str) if total_size_str else None

        downloaded_size = 0
        progress_step = 0
        if callback:
            callback({
                "status": "in_progress",
                "total_size": total_size,
                "downloaded_size": 0,
                "percent": 0,
                "time_elapsed": 0.0,
                "time_left": None,
            })
        with open(file_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded_size += len(chunk)
                    if total_size and callback:
                        percent = int(downloaded_size * 100 / total_size)
                        if percent >= (progress_step + 1) * 10 or percent == 100:
                            current_time = time.time()
                            time_elapsed = current_time - start_time
                            avg_speed = downloaded_size / time_elapsed if time_elapsed > 0 else 0
                            time_left = None
                            if avg_speed > 0 and total_size > 0:
                                remaining_size = total_size - downloaded_size
                                time_left = remaining_size / avg_speed
                            callback({
                                "status": "in_progress",
                                "total_size": total_size,
                                "downloaded_size": downloaded_size,
                                "percent": percent,
                                "time_elapsed": time_elapsed,
                                "time_left": time_left,
                            })
                            if percent < 100:
                                progress_step = percent // 10
        end_time = time.time()
        time_elapsed = end_time - start_time
        if callback:
            callback({
                "status": "completed",
                "total_size": total_size,
                "downloaded_size": downloaded_size,
                "percent": 100,
                "time_elapsed": time_elapsed,
                "time_left": 0.0,
            })
    return file_path


def simple_progress_callback(data: dict[str, Any]):
    status = data.get("status")
    if status == "in_progress":
        total = data["total_size"]
        downloaded = data["downloaded_size"]
        percent = data["percent"]
        elapsed = data["time_elapsed"]
        time_left = data["time_left"]
        total_mb = total / (1024 * 1024) if total else "???"
        downloaded_mb = downloaded / (1024 * 1024)
        time_left_str = f"{time_left:.1f} сек" if time_left is not None else "---"
        logger.info(f"Downloading: {percent:3d}% | Done: {downloaded_mb:.2f} MB / {total_mb:.2f} MB | Time: {elapsed:.1f} (Left: {time_left_str})")
    elif status == "completed":
        elapsed = data["time_elapsed"]
        logger.info(f"Downloading Done. Total time: {elapsed:.2f}sec.")
    elif status == "skipped":
        logger.info(f"File already exists: {data['file_path']}")


def upload_file_with_data(url: str, file_path: str, data: dict = None):
    try:
        with open(file_path, "rb") as f:
            files = {"file": (file_path.split("/")[-1], f)}
            response = requests.post(url, files=files, data=data)
            response.raise_for_status()
            return response.json()
    except FileNotFoundError:
        raise Exception(f"Failed: file '{file_path}' not found.")
    except requests.exceptions.RequestException as e:
        raise Exception(f"Upload failed: {e}")


def get_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        return s.getsockname()[1]


def download_dependency(relative_path: str, cache=True, **kwargs) -> str:
    url = f'https://storage.yandexcloud.net/agio-public/dep_packages/{relative_path}'
    if cache:
        dest_dir = cache_dir('dependencies')
        with requests.get(url, stream=True, params=kwargs.get('params'), allow_redirects=True) as response:
            file_hash  = response.headers.get('ETag').strip('"')
        cached_dir = dest_dir.joinpath(file_hash)
        if cached_dir.exists():
            logger.info(f"File already exists: {cached_dir}")
            return cached_dir.as_posix()
        with tempfile.TemporaryDirectory() as tmp_dir:
            stored_file = download_file(url, tmp_dir, **kwargs)
            unpack_archive(stored_file, cached_dir)
            logger.info(f"Unpacked {cached_dir}")
        return cached_dir.as_posix()
    else:
        dest_dir = tempfile.mkdtemp()
        return download_file(url, dest_dir, **kwargs)
