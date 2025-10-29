import hashlib
from pathlib import Path


def get_file_hash(file_path):
    hasher = hashlib.md5()
    with open(file_path, "rb") as f:
        while True:
            buf = f.read(65536)
            if not buf:
                break
            hasher.update(buf)
    has_sum = hasher.hexdigest()
    return has_sum


def get_folder_size(path: Path|str) -> int:
    return sum(f.stat().st_size for f in Path(path).rglob('*') if f.is_file())