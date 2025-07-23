import os
import requests
import json
import socket


def download_file(url: str, dest_dir: str, filename: str = None, params: dict = None,
                  headers=None, use_credentials = None, allow_redirects=False,
                  skip_exists: bool = False) -> str:
    """
    Скачивает файл по URL и сохраняет в указанную директорию.
    """
    filename = filename or url.split("/")[-1]
    file_path = os.path.join(dest_dir, filename)
    if skip_exists and os.path.exists(file_path):
        return file_path
    os.makedirs(dest_dir, exist_ok=True)

    with requests.get(url, stream=True, params=params, headers=headers, allow_redirects=allow_redirects) as response:
        response.raise_for_status()
        with open(file_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

    return file_path


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