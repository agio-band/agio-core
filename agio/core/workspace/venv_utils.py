import json
import subprocess
from typing import Callable

from packaging.specifiers import SpecifierSet
from packaging.version import Version
import logging

logger = logging.getLogger(__name__)


def get_site_packages_path(venv_python_path: str) -> str | None:
    try:
        result = subprocess.run(
            [venv_python_path, "-c", "import site, json; print(json.dumps(site.getsitepackages()))"],
            capture_output=True,
            text=True,
            check=True,
        )
        site_packages_list = json.loads(result.stdout.strip())
        return site_packages_list[0]
    except (subprocess.CalledProcessError, FileNotFoundError, json.JSONDecodeError) as e:
        return None


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
            raise ValueError(f"No matching versions found for {requirements_str}")

        best_version = max(matching_versions)
        return str(best_version)

    except Exception as e:
        print(f"Error while finding best available version: {e}")
        raise e


def check_current_python_version(required_version: str, current_version: str):
    specifier_set = SpecifierSet(required_version)
    current_version_obj = Version(current_version)
    is_match = current_version_obj in specifier_set

    if required_version.startswith("=="):
        required_base = required_version[2:]
        if str(current_version_obj).startswith(required_base):
            return True
    return is_match


find_best_available_version('3.13', '<=3.12', ['3.11.1', '3.12.0'])
