from pathlib import Path


def get_package_manager(venv_path: str|Path, py_executable: str|Path = None):
    cls = get_package_manager_class()
    return cls(venv_path, py_executable)


def get_package_manager_class():
    # TODO: choice from config
    from .uv import  UVPackageManager
    return UVPackageManager