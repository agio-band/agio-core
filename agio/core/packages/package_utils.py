import os
import sys
from pathlib import Path
from typing import Generator

from agio.core import api
from agio.core.packages import APackage, APackageLocal
from agio.core.packages.package_toolset import get_remote_repository_plugin
from agio.core.workspace.pkg_manager import get_package_manager, get_package_manager_class


def find_packages_roots() -> Generator:
    for path in sys.path:
        for mdl  in os.listdir(path):
            pkg_root = os.path.join(path, mdl)
            if APackageLocal.is_package_root(pkg_root):
                yield pkg_root


def register_package(package_repository_path: str):
    pkg = APackageLocal(package_repository_path)
    package_id = api.package.create_package(
        name=pkg.package_name
    )
    return package_id


def build_package(package_root: str|Path, **kwargs):
    pkg_manager = get_package_manager(Path(package_root))
    resp = pkg_manager.build_package(**kwargs)
    return resp


def make_release(package_repository_path: str, token: str = None, **kwargs):
    toolset = APackageLocal(package_repository_path)
    # check package is registered
    toolset.get_package()
    # check registered release
    release = toolset.get_release()
    if release:
        raise ValueError(f"Release {toolset.package_name} {toolset.package_version} "
                         f"already exists in agio repository")
    # build release
    repo = get_remote_repository_plugin(toolset.source_url, toolset.repository_api)
    release_data = repo.make_release(
        toolset,
        access_data={'token': token},
        **kwargs
    )
    return register_new_package_release(toolset, release_data)


def register_new_package_release(pkg: APackageLocal, data: dict = None, **kwargs):
    package = api.package.find_package(pkg.package_name)
    if not package:
        raise ValueError(f"Package {pkg.package_name} is not found")
    release_id = api.package.create_package_release(
        package_id=package['id'],
        version=pkg.package_version,
        label=pkg.label,
        description=pkg.description,
        assets={"whl": data['assets']},
        metadata={}
    )
    return release_id





def download_package_release(package_name: str, version: str, target_dir: str = None):
    pkg_manager = get_package_manager_class()
    return pkg_manager.download_package_release(package_name, version, target_dir)


# from packaging.requirements import Requirement
# from packaging.specifiers import SpecifierSet
# from packaging.version import Version
#


# def resolve_packages(packages: list[APackageInfo]):
#     agio_requires = []
#     for pkg in packages:
#         agio_requires.extend(pkg.get_agio_requirements())
#     resolved_versions = resolve_and_simplify_dependencies(agio_requires)


# def resolve_and_simplify_dependencies(packages: list[str]) -> list[str]:
#     constraints = defaultdict(list)
#
#     for pkg in packages:
#         try:
#             req = Requirement(pkg)
#             constraints[req.name].append(req.specifier)
#         except Exception as e:
#             raise ValueError(f"Invalid requirement '{pkg}': {e}")
#
#     conflicts = []
#     resolved = []
#
#     for name, specifiers in constraints.items():
#         combined = SpecifierSet()
#         for spec in specifiers:
#             combined &= spec
#
#         if not _is_satisfiable(combined):
#             readable = ", ".join(str(s) for s in specifiers if str(s))
#             conflicts.append(f"{name}: conflicting constraints: {readable}")
#         else:
#             spec_str = str(combined)
#             if spec_str:
#                 resolved.append(f"{name}{spec_str}")
#             else:
#                 resolved.append(name)
#
#     if conflicts:
#         raise ValueError("Dependency version conflicts found:\n" + "\n".join(conflicts))
#
#     return sorted(resolved)
#
#
# def _is_satisfiable(specs: SpecifierSet) -> bool:
#     test_versions = [
#         f"{major}.{minor}.{patch}"
#         for major in range(0, 3)
#         for minor in range(0, 5)
#         for patch in range(0, 3)
#     ]
#     for v in test_versions:
#         if Version(v) in specs:
#             return True
#     return False
