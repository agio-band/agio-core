from pathlib import Path
from typing import Generator
import os
import sys
from . import get_release_repository_plugin
from .package import APackage
from ..utils.network import download_file
from ..workspace.pkg_manager import get_package_manager, get_package_manager_class


def find_packages_roots() -> Generator:
    for path in sys.path:
        for mdl  in os.listdir(path):
            pkg_root = os.path.join(path, mdl)
            if APackage.is_package_root(pkg_root):
                yield pkg_root


def make_release(package_path: str, token: str = None):
    pkg = APackage(package_path)
    repo = get_release_repository_plugin(pkg.repository_url, pkg.data.get('repository_vendor'))
    if not repo:
        raise ValueError(f"Repository {pkg.repository_url} is not supported")
    return repo.make_release(
        pkg,
        access_data={'token': token},
        ignore_list=pkg.data.get('release_ignore')
    )


def build_package(package_root: str):
    path = Path(package_root)
    pkg_manager = get_package_manager(path)
    return pkg_manager.build_package()


def download_package_release(package_name: str, version: str, target_dir: str = None):
    pkg_manager = get_package_manager_class()
    return pkg_manager.download_package_release(package_name, version, target_dir)