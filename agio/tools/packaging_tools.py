from __future__ import annotations
import re
from typing import Callable, TYPE_CHECKING

from packaging.requirements import Requirement
from packaging.specifiers import InvalidSpecifier, Specifier, SpecifierSet
from packaging.version import InvalidVersion, Version

if TYPE_CHECKING:
    from agio.core.entities import package as p, package_release as r



class DependencyConflictError(Exception):
    pass


def version_matches(version: str|None, requirement: str|None) -> bool:
    """
    Check that the version satisfies ALL conditions of the requirement.
    For example ">=10,<15" matches 12, but not 9 and not 16.
    Empty requirement matches any version.
    """
    if not requirement:
        return True
    if not version:
        return False
    try:
        return Version(version) in SpecifierSet(requirement)
    except (InvalidVersion, InvalidSpecifier) as e:
        raise ValueError(f'Wrong version "{version}" or requirement "{requirement}": {e}') from e


def _specifiers_conflict(spec1: SpecifierSet, spec2: SpecifierSet) -> bool:
    """Checks if there is at least one version that satisfies both conditions."""
    # Extract all == constraints from both specifiers
    eq_versions = []
    for spec in list(spec1) + list(spec2):
        if spec.operator in ("==", "==="):
            eq_versions.append(Version(spec.version))

    # If there are exact version constraints, check if they satisfy the other specifier
    if eq_versions:
        for eq_ver in eq_versions:
            if eq_ver in spec1 and eq_ver in spec2:
                return False  # Found an exact version that satisfies both

    # Generate a wider range of test versions for other cases
    test_versions = [Version(f"{major}.{minor}.{patch}")
                     for major in range(0, 100)
                     for minor in range(0, 100)
                     for patch in range(0, 100)]

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
        raise DependencyConflictError(f"Version conflict: {spec1} and {spec2}")
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
    from agio.core.exceptions import PackageNotFound
    from agio.core.entities import package as p

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
            _, version_with_constraint = _split_name_constrain(release_name)
            all_versions = [rel.get_version() for rel in pkg.iter_releases()]
            version_to_install = find_best_available_version(None, version_with_constraint, all_versions)
            release = pkg.get_release(version_to_install)
            if not release:
                raise Exception(f'Dependency release "{name} v{version}" not found')
        releases_to_install.append(release)
    return _select_latest_releases(releases_to_install)


def _select_latest_releases(releases: list[r.APackageRelease]) -> list[r.APackageRelease]:
    """Deduplicates releases of the same package keeping only the highest version."""
    filtered = dict()
    for release in releases:
        pkg_name = release.get_package_name()
        if pkg_name not in filtered:
            filtered[pkg_name] = release
        else:
            if Version(release.get_version()) > Version(filtered[pkg_name].get_version()):
                filtered[pkg_name] = release
    return list(filtered.values())



def _requirement_allows_prereleases(specifier_set: SpecifierSet) -> bool:
    """Prereleases are selected only when the requirement mentions one explicitly,
    like ">=3.11rc1" or "==3.12.0b1"."""
    for specifier in specifier_set:
        try:
            if Version(specifier.version).is_prerelease:
                return True
        except InvalidVersion:  # wildcard "==3.11.*" or arbitrary "==="
            continue
    return False


def _version_matches_requirements(version: Version, specifier_set: SpecifierSet) -> bool:
    """Version must satisfy ALL specifiers in the set (empty set matches anything)."""
    for specifier in specifier_set:
        if version in specifier:
            continue
        # plain pin "==3.11" also accepts any 3.11.* release,
        # which strict PEP 440 equality doesn't cover
        if specifier.operator == "==" and "*" not in specifier.version:
            try:
                if version in Specifier(f"=={specifier.version}.*"):
                    continue
            except InvalidSpecifier:
                pass
        return False
    return True


def find_best_available_version(
        current_version_str: str|None,
        requirements_str: str,
        available_versions_str: list[str] | Callable[[], list[str]]) -> str|None:
    """
    Finds the highest version from available_versions_str that satisfies ALL
    conditions of requirements_str. Prereleases are ignored unless the requirement
    mentions one explicitly. Returns None if current_version_str already fits.
    """
    try:
        specifier_set = SpecifierSet(requirements_str)
        if current_version_str:
            current_version = Version(current_version_str)
            if current_version in specifier_set:
                return None

        if callable(available_versions_str):
            available_versions_str = available_versions_str()

        allow_prereleases = _requirement_allows_prereleases(specifier_set)
        matching_versions = []
        for version_str in available_versions_str:
            version = Version(version_str)
            if version.is_prerelease and not allow_prereleases:
                continue
            if _version_matches_requirements(version, specifier_set):
                matching_versions.append(version)

        if not matching_versions:
            raise ValueError(f"No matching versions found for {requirements_str}. available: {', '.join(available_versions_str)}")

        best_version = max(matching_versions)
        return str(best_version)

    except Exception as e:
        print(f"Error while finding best available version: {e}")
        raise e



def _split_name_constrain(name: str, strip_constraints: bool = False) -> tuple[str, str]:
    match = re.match(r"([a-zA-Z0-9_-]+)([<>=!~].*)", name)
    if match:
        package_name = match.group(1)
        version_constraint = match.group(2)
        if strip_constraints:
            version_constraint = re.sub(r"[^\w.]+", "", version_constraint)
        return package_name, version_constraint
    else:
        return name, ""
