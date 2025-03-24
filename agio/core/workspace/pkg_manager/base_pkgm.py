import os
import shutil
from pathlib import Path

from agio.core.utils.process_utils import start_process


class PackageManagerBase:

    def __init__(self, venv_path: str):
        self.path = venv_path

    @property
    def python_executable(self):
        return Path(self.path, 'bin/python' + ('.exe' if os.name == 'nt' else '')).as_posix()

    def install_package(self, package_name):
        raise NotImplementedError

    def uninstall_package(self, package_name):
        raise NotImplementedError

    def list_installed_packages(self):
        raise NotImplementedError

    def update_package(self, package_name):
        raise NotImplementedError

    def get_package_info(self, package_name):
        raise NotImplementedError

    def get_package_version(self, package_name):
        raise NotImplementedError

    def create_venv(self, venv_name):
        raise NotImplementedError

    def delete_venv(self, venv_path: str):
        shutil.rmtree(venv_path)

    def list_venvs(self):
        raise NotImplementedError

    def get_executable(self):
        raise NotImplementedError

    def call_cmd(self, cmd):
        cmd = [self.get_executable(), *cmd]
        return start_process(cmd, get_output=True)

    @classmethod
    def install_executable(cls):
        pass