from typing import Self, Iterator

from agio.core import api
from agio.core.api.utils import NOTSET
from agio.core.entities import Entity
from agio.core.workspace.revision import AWorkspaceRevision


class AWorkspace(Entity):
    @classmethod
    def get_data(cls, entity_id: str) -> Self:
        data = api.workspace.get_workspace(entity_id)
        if data:
            return cls(data)

    def update(self, name: str = NOTSET, description: str = None) -> None:
        if api.workspace.update_workspace(
            self.id,
            name=name,
            description=description,
        ):
            self.reload()

    @classmethod
    def iter(cls, company_id: str = None) -> Iterator[Self]:
        company_id = company_id or api.desk.get_current_company()['id']
        for data in api.workspace.iter_workspaces(company_id=company_id):
            yield cls(data)

    @classmethod
    def create(cls, company_id: str, name: str, description: str = NOTSET) -> Self:
        ws_id = api.workspace.create_workspace(
            company_id=company_id,
            name=name,
            description=description,
        )
        return cls(ws_id)

    def delete(self) -> bool:
        return api.workspace.delete_workspace(self.id)

    @classmethod
    def find(cls, company_id: str = None, name: str = NOTSET) -> Self:
        company_id = company_id or api.desk.get_current_company()['id']
        data = api.workspace.find_workspace(company_id=company_id, name=name)
        if data:
            return cls(data)

    def get_current_revision(self):
        revision = api.workspace.get_revision_by_workspace_id(self.id)
        if revision:
            return AWorkspaceRevision(revision)

    def get_toolset(self):
        from agio.core.workspace import AWorkspaceToolset

        return AWorkspaceToolset(self.get_current_revision())
