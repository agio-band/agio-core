import os
import sys
from agio.core.packages.package_base import APackage
from agio.core.utils.singleton import Singleton


class APackageHub(metaclass=Singleton):
    def __init__(self):
        self._packages = {}
        self.collect_packages()

    def add_package(self, package: APackage):
        if package.name in self._packages:
            raise ValueError(f"Package {package.name} already registered")
        self._packages[package.name] = package

    def get_package(self, name: str) -> APackage:
        return self._packages.get(name)

    def get_packages(self) -> dict[str, APackage]:
        return self._packages

    def get_package_names(self) -> list[str]:
        return list(self._packages.keys())

    def get_package_by_name(self, name: str) -> APackage:
        return self._packages.get(name)

    def get_package_list(self) -> list[APackage]:
        return list(self._packages.values())

    def package_exists(self, name: str) -> bool:
        return name in self._packages

    def collect_packages(self) -> None:
        self._packages.clear()
        for package in self.iter_packages():
            self.add_package(package)

    @classmethod
    def iter_packages(cls) -> list[APackage]:
        # TODO support zip packages
        loaded = set()
        for path in sys.path:
            if os.path.exists(path):
                if os.path.isdir(path):
                    for _path, _dirs, _files in os.walk(path):
                        if APackage.manifest_file_name in _files:
                            if APackage.is_package_root(_path):
                                if _path in loaded:
                                    continue
                                yield APackage(_path)
                                loaded.add(_path)
                                _dirs.clear()


