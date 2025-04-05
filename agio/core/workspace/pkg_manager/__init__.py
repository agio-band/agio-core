from pathlib import Path


def get_package_manager(venv_path: str|Path):
    cls = get_package_manager_class()
    return cls(venv_path)


def get_package_manager_class():
    # TODO: choice from config
    from .uv import  UVPackageManager
    return UVPackageManager