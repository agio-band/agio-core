from typing import Generator
import os
import sys
from .package_base import APackage
from ..utils.platform_info import detect_platform, get_platform_variables
from ..utils.network import download_file


def find_packages_roots() -> Generator:
    for path in sys.path:
        for mdl  in os.listdir(path):
            pkg_root = os.path.join(path, mdl)
            if APackage.is_package_root(pkg_root):
                yield pkg_root


import sys
import platform


def generate_wheel_filenames(package_name, package_version):
    python_version = f"cp{sys.version_info.major}{sys.version_info.minor}"
    abi = "none"
    system_platform = platform.system().lower()
    if system_platform == "linux":
        platform_tags = ["manylinux_x86_64", "manylinux1_x86_64", "manylinux2010_x86_64", "manylinux2014_x86_64"]
    elif system_platform == "windows":
        platform_tags = ["win_amd64", "win32"]
    elif system_platform == "darwin":
        platform_tags = ["macosx_10_9_x86_64", "macosx_10_15_x86_64"]
    else:
        platform_tags = ["any"]
    wheel_filenames = []
    for platform_tag in platform_tags:
        wheel_filenames.append(f"{package_name}-{package_version}-{python_version}-{abi}-{platform_tag}.whl")
    wheel_filenames.append(f"{package_name}-{package_version}-py3-none-any.whl")  # Универсальный для Python 3
    return wheel_filenames


def download_release(url: str, version: str, dest_dir: str = ".") -> str:
    """
    Основная функция: скачивает наиболее подходящий whl-файл релиза с GitHub.
    """
    platform_variables = get_platform_variables()

