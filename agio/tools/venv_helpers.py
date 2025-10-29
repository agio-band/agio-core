import json
import subprocess

from packaging.specifiers import SpecifierSet
from packaging.version import Version
import logging

logger = logging.getLogger(__name__)


def _get_site_packages_path(venv_python_path: str) -> str | None: # OLD VERSION
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


def get_site_packages_path(venv_python_path: str) -> str | None:
    try:
        result = subprocess.run(
            [venv_python_path, "-c", "import sysconfig; print(sysconfig.get_paths()['purelib'])"],
            capture_output=True,
            text=True,
            check=True,
        )
        site_package = result.stdout.strip()
        return site_package
    except (subprocess.CalledProcessError, FileNotFoundError, json.JSONDecodeError) as e:
        return None


def check_current_python_version(required_version: str, current_version: str):
    specifier_set = SpecifierSet(required_version)
    current_version_obj = Version(current_version)
    is_match = current_version_obj in specifier_set

    if required_version.startswith("=="):
        required_base = required_version[2:]
        if str(current_version_obj).startswith(required_base):
            return True
    return is_match

