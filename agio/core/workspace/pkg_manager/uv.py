import json
from agio.core.workspace.pkg_manager.base_pkgm import PackageManagerBase


class UVPackageManager(PackageManagerBase):
    def install_package(self, package_name):
        cmd = ['pip', 'install', '--prefix', self.path, package_name]
        self.call_cmd(cmd)

    def uninstall_package(self, package_name):
        cmd = ['pip', 'install', '--python', self.python_executable, package_name]
        self.call_cmd(cmd)

    def list_installed_packages(self, venv_path: str) -> dict:
        cmd = ['pip', 'list', '--python', self.python_executable, '-q' '--format', 'json']
        result = self.call_cmd(cmd)
        return json.loads(result)

    def update_package(self, package_name: str, venv_path: str):
        cmd = ['pip', 'install', '--upgrade', '--prefix', self.path, package_name]
        self.call_cmd(cmd)

    def get_package_version(self, package_name: str, venv_path: str) -> str | None:
        for prk in self.list_installed_packages(venv_path):
            if prk['name'] == package_name:
                return prk['version']

    def create_venv(self):
        self.call_cmd(['venv', self.path])

    def get_executable(self):
        return 'uv'

    @classmethod
    def install_executable(cls):
        pass