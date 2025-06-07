import os
import sys
from agio.core.packages.package import APackage
from agio.core.utils.singleton import Singleton
from agio.core.workspace.workspace import AWorkspace


class APackageHub(metaclass=Singleton):
    def __init__(self):
        self._packages = {}
        self.collect_packages()

    def add_package(self, package: APackage):
        if package.name in self._packages:
            raise ValueError(f"Package {package.name} already registered: {self._packages[package.name].root}")
        self._packages[package.name] = package

    @property
    def packages_count(self):
        return len(self._packages)

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
            if APackage.is_package_root(pkg_path) and pkg_path not in loaded:
                yield APackage(pkg_path)
                loaded.add(pkg_path)
