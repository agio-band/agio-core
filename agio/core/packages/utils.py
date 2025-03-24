import os
import sys
from typing import Generator
from .package_base import APackage


def find_packages() -> Generator:
    for path in sys.path:
        for mdl  in os.listdir(path):
            pkg_root = os.path.join(path, mdl)
            if APackage.is_package_root(pkg_root):
                yield APackage(pkg_root)

