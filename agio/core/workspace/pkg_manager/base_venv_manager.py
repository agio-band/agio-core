import os
import shutil
import logging
from pathlib import Path

from agio.core.packages.package_base import APackage
from agio.core.utils.process import start_process
from agio.core.workspace import venv_utils

logger = logging.getLogger(__name__)


class VenvManagerBase:

    def __init__(self, venv_path: str):
        self.path = Path(venv_path).expanduser().as_posix()

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

    def iter_packages(self):
        site_packages_path = venv_utils.get_site_packages_path(self.python_executable)
        if not site_packages_path:
            return
        site_packages_path = Path(site_packages_path)
        for package in site_packages_path.glob(f'*/{APackage.manifest_file_name}'):
            yield APackage.from_path(package.as_posix())


    def create_venv(self, venv_name):
        raise NotImplementedError

    def delete_venv(self):
        shutil.rmtree(self.path)

    def list_venvs(self):
        raise NotImplementedError

    def get_executable(self):
        raise NotImplementedError

    def call_cmd(self, cmd):
        cmd = [self.get_executable(), *cmd]
        logger.debug(f'Running command: {" ".join(cmd)}')
        return start_process(cmd, get_output=True)

    @classmethod
    def get_venvs_installation_path(cls):
        return Path('~.agio/venvs').expanduser().as_posix() # TODO grom config

    @classmethod
    def get_package_manager_installation_path(cls):
        return Path('~/.agio/pkg-mng').expanduser().as_posix()

    @classmethod
    def install_executable(cls):
        pass