import os
import webbrowser
from pathlib import Path


def expand_windows_path(path):
    """Expand windows 8.3 path to long"""
    if not os.name == 'nt':
        return path

    import ctypes
    from ctypes import wintypes

    GetLongPathNameW = ctypes.windll.kernel32.GetLongPathNameW
    GetLongPathNameW.argtypes = [wintypes.LPCWSTR, wintypes.LPWSTR, wintypes.DWORD]
    GetLongPathNameW.restype = wintypes.DWORD

    buf = ctypes.create_unicode_buffer(260)
    result = GetLongPathNameW(path, buf, len(buf))
    if result > 0:
        return buf.value
    else:
        return path


def open_path(path):
    path = Path(path)
    if path.is_dir():
        webbrowser.open(path.as_posix())
    elif path.is_file():
        webbrowser.open(path.as_posix())
    else:
        raise FileNotFoundError(path)
