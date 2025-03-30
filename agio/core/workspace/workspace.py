from functools import cached_property
from uuid import UUID

from agio.core.exceptions import WorkspaceNotExists
from agio.core.packages.package_base import APackage
from agio.core.workspace import pkg_manager, request_data


class AWorkspace:
    def __init__(self, workspace_id: str|UUID, data: dict = None):
        self.id = workspace_id
        self._data = data or request_data.load_workspace_data(workspace_id)

    def __str__(self):
        return self.name or self.id

    def __repr__(self):
        return f'<Workspace "{str(self)}">'

    @property
    def name(self):
        return self._data.get('name')

    @property
    def root(self):
        return request_data.get_workspaces_installation_root() / str(self.id)

    @cached_property
    def venv_manager(self):
        return pkg_manager.get_package_manager(self.root)

    def get_package_list_to_install(self) -> list:
        packages = []
        for pkg in self._data.get('packages', []):
            package = APackage(**pkg)
            packages.append(package.installation_name)
        return packages

    def iter_installed_packages(self):
        yield from self.venv_manager.iter_packages()

    def iter_packages(self):
        for pkg in self._data.get('packages', []):
            yield APackage(**pkg)

    def get_package(self, name):
        pass

    def get_launch_envs(self):
        return {
            'AGIO_WORKSPACE_ID': str(self.id),
            'VIRTUAL_ENV': self.root.as_posix()
        }

    def get_pyexecutable(self) -> str:
        return self.venv_manager.python_executable

    def collect_stat(self):
        """
        File sizes
        Creation date
        Package count
            python libs
            agio packages
        """
        pass

    def exists(self):
        return self.root.exists()

    def install(self, force: bool = False):
        if self.exists():
            if force:
                self.venv_manager.delete_venv()
            else:
                return False
        self.venv_manager.create_venv()
        packages = self.get_package_list_to_install()
        self.venv_manager.install_packages(packages)


    def remove(self) -> bool:
        if self.exists():
            self.venv_manager.delete_venv()
            return True
        return False

    def reinstall(self):
        self.remove()
        self.install()

    def update(self):
        if not self.exists():
            raise WorkspaceNotExists('Workspace not installed')
        packages = self.get_package_list()
        self.venv_manager.install_packages(packages)
