from . import request_data
from agio.core.workspace.workspace import AWorkspace
from ..exceptions import WorkspaceNotExists


class WSManager:
    api_url = 'http://0.0.0.0:8002/workspace'

    def get_workspace_installation_info(self, workspace_name: str):
        ...

    def install(self, workspace_id: str):
        data = request_data.load_workspace_data(workspace_id)
        ws_id = request_data.create_workspace(workspace_id, data['packages'])
        return AWorkspace(ws_id, data)

    def is_installed(self, workspace_id: str):
        try:
            ws = self.get_workspace(workspace_id)
            return ws.root.exists()
        except WorkspaceNotExists:
            return False

    def is_up_to_date(self, workspace_id: str):
        pass

    def update(self, workspace_id: str, data: dict):
        return request_data.update_workspace(workspace_id, data)

    def delete(self, workspace_id: str):
        return request_data.delete_workspace(workspace_id)

    def get_workspace(self, workspace_id: str):
        return AWorkspace(workspace_id)

    def list_workspaces(self):
        return request_data.list_workspaces()

    def load_workspace_data(self, workspace_id: str):
        return request_data.load_workspace_data(workspace_id)