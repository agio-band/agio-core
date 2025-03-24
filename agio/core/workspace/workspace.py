from pathlib import Path
from uuid import UUID

from agio.core.workspace import ws_utils


class AWorkspace:
    def __init__(self, workspace_id: UUID|str, data: dict = None):
        self.id = workspace_id
        self._data = data or ws_utils.load_workspace_data(workspace_id)

    def __str__(self):
        return self.name or self.id

    def __repr__(self):
        return f'<Workspace "{str(self)}">'

    @property
    def name(self):
        return self._data.get('name')

    @property
    def root(self):
        return ws_utils.get_workspaces_installation_root() / str(self.id)

    def get_package_list(self):
        pass

    def get_package(self, name):
        pass

    def get_launch_envs(self):
        pass

    def get_pyexecutable(self):
        pass

    def collect_stat(self):
        """
        File sizes
        Creation date
        Package count
            python libs
            agio packages
        """
        pass
