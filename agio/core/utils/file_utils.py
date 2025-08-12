import hashlib


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