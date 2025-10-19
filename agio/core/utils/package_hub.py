from __future__ import annotations
import glob
import os
import sys
from typing import Generator

from agio.core.pkg import package
from agio.core.utils.singleton import Singleton


class APackageHub(metaclass=Singleton):
    def __init__(self):
        self._packages = {}
        self.collect_packages()

    def add_package(self, package_manager: package.APackageManager):
        if package_manager.package_name in self._packages:
            raise ValueError(f"Package {package_manager.package_name} already registered: {self._packages[package_manager.package_name].root}")
        self._packages[package_manager.package_name] = package_manager

    @property
    def packages_count(self):
        return len(self._packages)

    def get_package(self, name: str) -> package.APackage:
        return self._packages.get(name)

    def get_packages(self) -> dict[str, package.APackage]:
        return self._packages

    def get_package_names(self) -> list[str]:
        return list(self._packages.keys())

    def get_package_by_name(self, name: str) -> package.APackage:
        return self._packages.get(name)

    def get_package_list(self) -> list[package.APackage]:
        return list(self._packages.values())

    def package_exists(self, name: str) -> bool:
        return name in self._packages

    def collect_packages(self) -> None:
        self._packages.clear()
        for package in self.iter_packages():
            self.add_package(package)

    @classmethod
    def iter_packages(cls) -> Generator[package.APackageManager, None, None]:
        # TODO support zip packages

        def iter_importable_packages():
            seen = set()
            for sys_path in sys.path:
                if not os.path.isdir(sys_path):
                    continue
                for entry in os.listdir(sys_path):
                    if entry.startswith(('_', '.')):
                        continue
                    full_path = os.path.join(sys_path, entry)
                    if os.path.isdir(full_path) and entry not in seen:
                        seen.add(entry)
                        yield full_path

        loaded = set()
        for pkg_path in iter_importable_packages():
            if package.APackageManager.is_package_root(pkg_path) and pkg_path not in loaded:
                yield package.APackageManager(pkg_path)
                loaded.add(pkg_path)

    def collect_callbacks(self):
        for pkg in self.iter_packages():
            for pattern in pkg.get_callbacks():
                for file in glob.glob(pattern, recursive=True):
                    if os.path.isfile(file):
                        yield file, pkg