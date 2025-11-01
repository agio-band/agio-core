import shutil
from pathlib import Path

from agio.tools import app_dirs


def get_files_from_cache(key) -> list[Path]:
    file_cache_dir = app_dirs.cache_dir('cached-files', key)
    if file_cache_dir.exists():
        for file in file_cache_dir.rglob('*'):
            yield file, file.relative_to(file_cache_dir)
    else:
        raise FileNotFoundError('No cached files found')


def save_file_to_cache(key, src_file, save_path) -> (Path, Path):
    file_cache_dir = app_dirs.cache_dir('cached-files', key)
    file_cache_dir.mkdir(parents=True, exist_ok=True)
    full_save_path = file_cache_dir / save_path
    if full_save_path.exists():
        full_save_path.unlink()
    shutil.copy(src_file, full_save_path)
    return full_save_path, full_save_path.relative_to(file_cache_dir)


def clear_cache(key):
    file_cache_dir = app_dirs.cache_dir('cached-files', key)
    if file_cache_dir.exists():
        shutil.rmtree(file_cache_dir)