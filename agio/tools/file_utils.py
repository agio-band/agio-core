import fnmatch
import hashlib
import logging
import os
import shutil
from pathlib import Path
from typing import Union

logger = logging.getLogger(__name__)


def get_file_hash(file_path) -> str:
    """Compute md5 file hash"""
    hasher = hashlib.md5()
    with open(file_path, "rb") as f:
        while True:
            buf = f.read(65536)
            if not buf:
                break
            hasher.update(buf)
    has_sum = hasher.hexdigest()
    return has_sum


def get_folder_size(path: Union[Path, str], ignore_links: bool = False) -> int:
    """
    Returns folder size in bytes.

    :param path:
    :param ignore_links: If True — ignore symlinks and hardlinks (st_nlink > 1)
    :return: size in bytes (int)
    """
    total_size = 0
    path = Path(path)

    def scan_dir(directory: Path):
        nonlocal total_size
        try:
            with os.scandir(directory) as entries:
                for entry in entries:
                    try:
                        if entry.is_dir(follow_symlinks=False):
                            scan_dir(Path(entry.path))
                        elif entry.is_file(follow_symlinks=False):
                            stat = entry.stat(follow_symlinks=False)
                            if ignore_links:
                                if entry.is_symlink() or stat.st_nlink > 1:
                                    continue

                            total_size += stat.st_size
                    except (OSError, PermissionError):
                        logger.warning('Can not read path %s', directory)
                        continue
        except (OSError, PermissionError):
            logger.warning('Can not read path %s', directory)

    scan_dir(path)
    return total_size


def copy_tree_with_ignore_file(source_dir: str, target_dir: str, ignore_file_path: str | None = None):
    """
    Copy tree from source_dir to target_dir with ignore file
    By default .gitignore will use
    """
    source_dir = Path(source_dir)
    target_dir = Path(target_dir)

    ignore_file = Path(ignore_file_path) if ignore_file_path else source_dir / ".gitignore"

    if ignore_file.exists():
        ignore_patterns = [
            line.strip()
            for line in ignore_file.read_text().splitlines()
            if line.strip() and not line.startswith("#")
        ]
    else:
        ignore_patterns = []

    ignore_patterns.extend([".venv", ".git", "__pycache__"])

    def is_ignored(path: Path) -> bool:
        """Chack patterns."""
        rel_path = str(path.relative_to(source_dir)).replace("\\", "/")
        for pattern in ignore_patterns:
            normalized = pattern.rstrip("/")

            if rel_path == normalized or rel_path.startswith(normalized + "/"):
                return True

            if fnmatch.fnmatch(rel_path, pattern):
                return True

        return False

    for root, dirs, files in os.walk(source_dir):
        root_path = Path(root)
        rel_root = root_path.relative_to(source_dir)

        dirs[:] = [d for d in dirs if not is_ignored(root_path / d)]

        for f in files:
            file_path = root_path / f
            if is_ignored(file_path):
                continue

            dest_path = target_dir / rel_root / f
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(file_path, dest_path)

