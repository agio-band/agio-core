import json
import os
import platform
import re
import shutil
import stat
import tarfile
import tempfile
import zipfile
import logging
from functools import lru_cache
from pathlib import Path
import requests
from .. import venv_utils

from .pkg_manager_base import PackageManagerBase
from agio.core.utils.process_utils import start_process

logger = logging.getLogger(__name__)


class UVPackageManager(PackageManagerBase):
    """
    uv python install 3.12
    uv python install '>=3.8,<3.10'
    """

    @property
    def venv_path(self):
        return Path(self.path, '.venv')

    def install_package(self, package_name):
        cmd = ['pip', 'install', package_name]
        self.run(cmd)

    def install_packages(self, *packages: str, **kwargs):
        cmd = ['pip', 'install']
        if kwargs.get('no_cache'):
            cmd.append('--no-cache')
        cmd.extend(packages)
        self.run(cmd)

    def uninstall_package(self, package_name):
        cmd = ['pip', 'uninstall', package_name]
        self.run(cmd)

    def list_installed_packages(self) -> dict:
        cmd = ['pip', 'list', '-q', '--format', 'json']
        result = self.run(cmd)
        return json.loads(result)

    def update_package(self, package_name: str):
        cmd = ['pip', 'install', '--upgrade', package_name]
        self.run(cmd)

    def get_package_version(self, package_name: str) -> str | None:
        for prk in self.list_installed_packages():
            if prk['name'] == package_name:
                return prk['version']

    def _get_latest_version(self, versions: list[str], pre_releases=False) -> str | None:
        sorted_versions = sorted(versions, key=lambda vers: re.search(r"\d+\.\d+\.\d+", vers).groups())
        if not pre_releases:
            sorted_versions = [x for x in sorted_versions if not re.search(r"[a-z]", x)]
        return sorted_versions[0] if sorted_versions else None

    def _get_available_py_version(self, py_version: str = None) -> str | None:
        available_versions = [x['version'] for x in self.get_available_python_versions()]
        if py_version:
            py_version = venv_utils.find_best_available_version(
                None,
                py_version,
                available_versions
            )
        else:
            py_version = self._get_latest_version(available_versions)
        return py_version

    def create_venv(self, py_version: str|None = None):
        if self._custom_python_executable:
            py_version = self._custom_python_executable
        else:
            py_version = self._get_available_py_version(py_version)
            if py_version:
                # py_version = '==' + py_version  # force match version
                if py_version not in self.get_installed_python_versions():
                    logger.info('Installing python version: %s', py_version)
                    cmd = ['python', 'install', '==' + py_version]
                    self.run(cmd, workdir=Path.home().as_posix())
            else:
                raise RuntimeError('No python version available')
        logger.info('Create venv with python: %s', py_version)
        cmd = ['init', '--bare']
        cmd.extend(['--python', py_version])
        self.path.mkdir(parents=True, exist_ok=True)
        self.run(cmd, workdir=self.path.as_posix())
        self.run(['venv', '--python', py_version], workdir=self.path.as_posix())
        logger.info('Create venv with version %s: %s', py_version, self.path)

    def venv_exists(self):
        return Path(self.venv_path, 'pyvenv.cfg').exists()

    def delete_venv(self):
        venv_path = self.path / '.venv'
        if venv_path.exists():
            shutil.rmtree(venv_path)

    def get_executable(self):
        executable = Path(self.get_package_manager_installation_path(), 'uv', 'uv' + ('.exe' if os.name == 'nt' else ''))
        if not executable.exists():
            return self.install_executable()
        return executable.as_posix()

    @classmethod
    def install_executable(cls):
        install_path = Path(cls.get_package_manager_installation_path(), 'uv').as_posix()
        return _install_uv(install_path)

    def build_package(self, cleanup=True, **kwargs):
        if self._custom_python_executable:
            raise RuntimeError('Dont use this method with custom python interpreter')
        self.run(['pip', 'install', 'build'])
        dist_path = self.path/'dist'
        if dist_path.exists():
            shutil.rmtree(dist_path)
        self.run(['build', '--wheel'])
        if cleanup and not kwargs.get('no_cleanup'):
            self.cleanup_build_files()
        return dist_path

    def cleanup_build_files(self):
        to_delete = ['*egg-info', 'build']
        for name in to_delete:
            for path in self.path.glob(name):
                if path.is_dir():
                    shutil.rmtree(path)
                else:
                    path.unlink()

    def get_installed_python_versions(self):
        all_version = self.get_available_python_versions()
        return [v['version'] for v in all_version if v['path']]

    @lru_cache
    def get_available_python_versions(self):
        cmd = [self.get_executable(), 'python', 'list', '--output-format', 'json']
        result = start_process(cmd, get_output=True)
        if result:
            return json.loads(result)

def _install_uv(install_dir: str, version: str = "latest") -> str:
    system = platform.system().lower()
    architecture = platform.machine().lower()
    executable_name = "uv.exe" if system == "windows" else "uv"
    install_path = os.path.join(install_dir, executable_name)

    os.makedirs(install_dir, exist_ok=True)

    # Check if uv is already installed
    if os.path.exists(install_path):
        os.remove(install_path)

    # Determine the correct artifact name (same as before)
    if system == "windows":
        if architecture == "x86_64" or architecture == "amd64":
            artifact_name = "uv-x86_64-pc-windows-msvc.zip"
        elif architecture == "i686" or architecture == "i386":
            artifact_name = "uv-i686-pc-windows-msvc.zip"
        elif architecture.startswith("arm"):
            artifact_name = "uv-aarch64-pc-windows-msvc.zip"
        else:
            raise RuntimeError(f"Unsupported Windows architecture: {architecture}")
    elif system == "linux":
        if architecture == "x86_64" or architecture == "amd64":
            artifact_name = "uv-x86_64-unknown-linux-gnu.tar.gz"
        elif architecture == "i686" or architecture == "i386":
            artifact_name = "uv-i686-unknown-linux-gnu.tar.gz"
        elif architecture.startswith("arm"):
            if architecture.endswith("hf") or "v7" in architecture:
                artifact_name = "uv-armv7-unknown-linux-gnueabihf.tar.gz"
            else:
                artifact_name = "uv-aarch64-unknown-linux-gnu.tar.gz"
        elif architecture.startswith("riscv64"):
            artifact_name = "uv-riscv64gc-unknown-linux-gnu.tar.gz"
        else:
            raise RuntimeError(f"Unsupported Linux architecture: {architecture}")
    elif system == "darwin":
        if architecture == "x86_64" or architecture == "amd64":
            artifact_name = "uv-x86_64-apple-darwin.tar.gz"
        elif architecture.startswith("arm"):
            artifact_name = "uv-aarch64-apple-darwin.tar.gz"
        else:
            raise RuntimeError(f"Unsupported macOS architecture: {architecture}")
    else:
        raise RuntimeError(f"Unsupported operating system: {system}")

    # Construct the download URL (same as before)
    if version == "latest":
        releases_url = "https://api.github.com/repos/astral-sh/uv/releases/latest"
        try:
            response = requests.get(releases_url)
            response.raise_for_status()
            release_info = response.json()
            tag_name = release_info["tag_name"]
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Failed to fetch latest release information: {e}") from e
    else:
        tag_name = f"v{version}"

    download_url = f"https://github.com/astral-sh/uv/releases/download/{tag_name}/{artifact_name}"
    logger.debug(f"Downloading {download_url}...")

    os.makedirs(install_dir, exist_ok=True)

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_file = os.path.join(temp_dir, artifact_name)

        try:
            response = requests.get(download_url, stream=True)
            response.raise_for_status()
            with open(temp_file, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Failed to download uv: {e}") from e

        logger.debug(f"Extracting to {install_dir}...")
        try:
            if artifact_name.endswith(".zip"):
                with zipfile.ZipFile(temp_file, "r") as zip_ref:
                    zip_ref.extractall(temp_dir)
            elif artifact_name.endswith(".tar.gz"):
                with tarfile.open(temp_file, "r:gz") as tar_ref:
                    tar_ref.extractall(temp_dir)
            else:
                raise RuntimeError(f"Unsupported archive format: {artifact_name}")
        except Exception as e:
            raise RuntimeError(f"Failed to extract uv: {e}") from e

        # Find the executable (using the new function)
        def find_executable(directory: str, executable_name: str) -> str | None:
            for root, _, files in os.walk(directory):
                if executable_name in files:
                    return os.path.join(root, executable_name)
            return None

        extracted_executable = find_executable(temp_dir, executable_name)

        if extracted_executable is None:  # More robust check
            raise RuntimeError(f"Extracted executable not found in {temp_dir}")

        shutil.move(extracted_executable, install_path)

        if system != "windows":
            os.chmod(install_path,
                     stat.S_IXUSR | stat.S_IRUSR | stat.S_IWUSR | stat.S_IXGRP | stat.S_IRGRP | stat.S_IXOTH | stat.S_IROTH)

    logger.info(f"uv ({tag_name}) installed to {install_path}")
    return install_path
