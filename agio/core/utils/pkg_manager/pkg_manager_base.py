import inspect
import os
import logging
import subprocess
from pathlib import Path
import shlex

from agio.core.pkg import APackageManager
from agio.core.utils.process_utils import start_process
from agio.core.utils import venv_utils

try:
    import tomllib as toml
except ModuleNotFoundError:
    import tomli as toml

logger = logging.getLogger(__name__)


class PackageManagerBase:

    def __init__(self, package_root: str|Path, custom_python_executable: str|Path = None,
                 custom_py_version: str|Path = None) -> None:
        self.path = Path(package_root)
        self.path.mkdir(exist_ok=True, parents=True)
        self._custom_python_executable = None
        self._custom_py_version = custom_py_version
        if custom_python_executable:
            if not Path(custom_python_executable).exists():
                raise FileNotFoundError(f"File {custom_python_executable} does not exist")
            self._custom_python_executable = custom_python_executable

    @property
    def python_executable(self):
        return Path(
            self.bin_dir_path,
            'python' +
            ('.exe' if os.name == 'nt' else '')
        ).as_posix()

    @property
    def bin_dir_path(self):
        if not self.venv_exists():
            raise FileNotFoundError(f'venv is not installed yet: {self.path}')
        bit_dir = 'Scripts' if os.name == 'nt' else 'bin'
        return Path(
            self.path,
            f'.venv/{bit_dir}'
        ).as_posix()

    @property
    def site_packages(self):
        if not self.venv_exists():
            raise FileNotFoundError(f'venv is not installed yet: {self.path}')
        return self.run(['run', 'python', '-c' "import sysconfig; print(sysconfig.get_paths()['purelib'])"],
                        get_output=True).strip()

    @property
    def pyproject_file_path(self):
        return Path(self.path, 'pyproject.toml')

    def get_pyproject_file_data(self):
        if not self.pyproject_file_path.exists():
            return {}
        with open(self.pyproject_file_path, 'r') as f:
            return toml.load(f)

    def get_python_version(self, full=False):
        if not self.venv_exists():
            return None
        cmd = [self.python_executable, '--version']
        result = subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True)
        version = result.split(' ')[-1]
        if full:
            return version
        return '.'.join(version.split('.')[:2])

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
        for package in site_packages_path.glob(f'*/{APackageManager.info_file_name}'):
            yield APackageManager(package.parent.as_posix())

    def create_venv(self):
        raise NotImplementedError

    def venv_exists(self):
        raise NotImplementedError

    def delete_venv(self):
        raise NotImplementedError

    def get_executable(self):
        raise NotImplementedError

    def get_installed_python_versions(self):
        raise NotImplementedError

    def run(self, cmd, workdir=None, **kwargs):
        if not self.venv_exists():
            caller_name = inspect.stack()[1].function
            if caller_name != 'create_venv':
                self.create_venv()
        if isinstance(cmd, str):
            cmd = shlex.split(cmd)
        cmd = list(map(str, [self.get_executable(), *cmd]))
        workdir = workdir or str(self.path)
        logger.debug(f'Running command: {" ".join(cmd)}')
        logger.debug(f'In directory: {workdir}')
        kwargs.setdefault('get_output', False)
        return start_process(cmd, workdir=workdir, clear_env=['VIRTUAL_ENV'], **kwargs)

    @classmethod
    def get_package_manager_installation_path(cls):
        return Path('~/.agio/pkg-mng').expanduser().as_posix()  # TODO from config

    @classmethod
    def install_executable(cls):
        pass

    def build_package(self):
        """Use package repository root instead venv root"""
        raise NotImplementedError