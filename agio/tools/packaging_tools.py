import re
from typing import Callable

from packaging.requirements import Requirement
from packaging.specifiers import SpecifierSet
from packaging.version import Version

from agio.core.entities import package as p, package_release as r
from agio.core.exceptions import PackageNotFound


class DependencyConflictError(Exception):
    pass


def _specifiers_conflict(spec1: SpecifierSet, spec2: SpecifierSet) -> bool:
    """Checks if there is at least one version that satisfies both conditions."""
    test_versions = [Version(f"{major}.{minor}.{patch}")
                     for major in range(0, 10)
                     for minor in range(0, 10)
                     for patch in range(0, 10)]

    for v in reversed(test_versions):  # check from new to old
        if v in spec1 and v in spec2:
            return False  # intersection found, no conflict
    return True  # no intersection, conflict!


def _simplify_specifiers(spec: SpecifierSet) -> SpecifierSet:
    """
    Simplifies the set of specifiers by removing duplicates and leaving only the most restrictive ones.
    For example: ">=0.1.0,>=0.2.0" => ">=0.2.0"
    """
    specs = list(spec)
    if not specs:
        return spec

    ge_versions = [s for s in specs if s.operator in (">", ">=")]
    le_versions = [s for s in specs if s.operator in ("<", "<=")]
    eq_versions = [s for s in specs if s.operator in ("==", "===")]

    # if there are specific versions ==, leave only the newest ones
    if eq_versions:
        max_ver = max(Version(s.version) for s in eq_versions)
        return SpecifierSet(f"=={max_ver}")

    # leave the "newest" lower boundary (>=)
    ge_spec = None
    if ge_versions:
        ge_spec = max(ge_versions, key=lambda s: Version(s.version))

    # leave the "lowest" upper limit (<=)
    le_spec = None
    if le_versions:
        le_spec = min(le_versions, key=lambda s: Version(s.version))

    simplified = []
    if ge_spec:
        simplified.append(str(ge_spec))
    if le_spec:
        simplified.append(str(le_spec))

    return SpecifierSet(",".join(simplified))


def _merge_specifiers(spec1: SpecifierSet, spec2: SpecifierSet) -> SpecifierSet:
    """combines two sets of specifiers, checking for conflict."""
    if _specifiers_conflict(spec1, spec2):
        raise DependencyConflictError(f"Конфликт версий: {spec1} и {spec2}")
    combined = SpecifierSet(str(spec1) + "," + str(spec2))
    return _simplify_specifiers(combined)


def resolve_dependencies(packages: dict) -> list[str]:
    """
    Resolves dependencies between packages and returns a list of the latest valid versions
    """
    deps = {}

    for pkg, deps_list in packages.items():
        for dep_str in deps_list:
            req = Requirement(dep_str)
            name = req.name
            spec = req.specifier or SpecifierSet("")

            if name not in deps:
                deps[name] = spec
            else:
                deps[name] = _merge_specifiers(deps[name], spec)

    result = []
    for name, spec in deps.items():
        spec_str = str(spec) if str(spec) else ""
        result.append(f"{name}{spec_str}")

    return sorted(result)


def collect_packages_to_install(packages: list[p.APackage|r.APackageRelease|str]) -> list[r.APackageRelease]:
    """
    Collect and check packages.
    Collect and resolve dependencies
    return list of package names and versions [package_name==0.0.0, ...]
    """
    releases_to_install = []
    for pkg in packages:
        if isinstance(pkg, p.APackageRelease):
            releases_to_install.append(pkg)
        elif isinstance(pkg, p.APackage):
            releases_to_install.append(pkg.latest_release())
        elif isinstance(pkg, str):
            package_name, version = _split_name_constrain(pkg)
            if version:
                package = p.APackage.find(package_name)
                if not package:
                    raise PackageNotFound()
                all_versions = [rel.get_version() for rel in package.iter_releases()]
                version_to_install = find_best_available_version(None, version, all_versions)
                rel = package.get_release(version_to_install)
                releases_to_install.append(rel)
            else:
                releases_to_install.append(p.APackage.find(package_name).latest_release())
    all_dependencies = {}
    for release in releases_to_install:
        deps = release.get_dependencies()
        if deps:
            all_dependencies[release.get_package_name()] = deps
    resolved_dependencies = resolve_dependencies(all_dependencies)
    for release_name in resolved_dependencies:
        name, version = _split_name_constrain(release_name, strip_constraints=True)
        pkg = p.APackage.find(name)
        if not pkg:
            raise Exception(f'Dependency package "{name}" not found')
        release = pkg.get_release(version)
        if not release:
            raise Exception(f'Dependency release "{name} v{version}" not found')
        releases_to_install.append(release)
    return releases_to_install



def find_best_available_version(current_version_str: str|None,
                                requirements_str: str,
                                available_versions_str: list[str] | Callable[[], list[str]]) -> str |None:
    try:
        specifier_set = SpecifierSet(requirements_str)
        if current_version_str:
            current_version = Version(current_version_str)
            if current_version in specifier_set:
                return None

        if callable(available_versions_str):
            available_versions_str = available_versions_str()

        available_versions = [Version(v) for v in available_versions_str]
        matching_versions = []

        for available_version in available_versions:
            for specifier in specifier_set:
                if specifier.operator == "==":
                    required_base = str(specifier.version)
                    available_base = str(available_version)
                    if available_base.startswith(required_base):
                        matching_versions.append(available_version)
                        break
                elif available_version in specifier:
                    matching_versions.append(available_version)
                    break

        if not matching_versions:
            raise ValueError(f"No matching versions found for {requirements_str}. available: {', '.join(available_versions_str)}")

        best_version = max(matching_versions)
        return str(best_version)

    except Exception as e:
        print(f"Error while finding best available version: {e}")
        raise e



def _split_name_constrain(name: str, strip_constraints: bool = False) -> (str, str):
    match = re.match(r"([a-zA-Z0-9_-]+)([<>=!~].*)", name)
    if match:
        package_name = match.group(1)
        version_constraint = match.group(2)
        if strip_constraints:
            version_constraint = re.sub(r"[^\w.]+", "", version_constraint)
        return package_name, version_constraint
    else:
        return name, ""
