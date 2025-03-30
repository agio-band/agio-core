import os

import requests


def download_file(url: str, dest_dir: str) -> str:
    """
    Скачивает файл по URL и сохраняет в указанную директорию.
    """
    os.makedirs(dest_dir, exist_ok=True)
    filename = url.split("/")[-1]
    file_path = os.path.join(dest_dir, filename)

    with requests.get(url, stream=True) as response:
        response.raise_for_status()
        with open(file_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

    return file_path
