from pathlib import Path


def get_package_manager(venv_path: str|Path):
    cls = get_package_manager_class()
    return cls(venv_path)

def get_package_manager_class():
    from .uv import  UVVenvManager
    return UVVenvManager