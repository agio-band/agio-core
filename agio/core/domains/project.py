from typing import Self, Iterator
from uuid import UUID

from agio.core import api
from agio.core import settings
from agio.core.domains import DomainBase, AWorkspace
from agio.core.domains import company


class AProject(DomainBase):
    domain_name = "project"

    @property
    def code(self):
        return self.data["code"]

    @property
    def name(self):
        return self.data["name"]

    @classmethod
    def get_data(cls, object_id: str) -> dict:
        return api.track.get_project(object_id)

    def update(self, state: str = None, fields: dict = None, workspace_id: str|UUID = None) -> bool:
        resp = api.track.update_project(self.id, state=state, fields=fields, workspace_id=workspace_id)
        self.reload()
        return resp

    @classmethod
    def iter(cls, company_id: str|UUID, **kwargs) -> Iterator[Self]:
        for prj_data in api.track.iter_projects(company_id=company_id, **kwargs):
            yield cls(prj_data)

    @classmethod
    def create(cls, **kwargs) -> Self:
        raise NotImplementedError()

    def delete(self) -> None:
        raise NotImplementedError()

    @classmethod
    def find(cls, company_id: str, **kwargs):
        data = api.track.find_project(company_id, **kwargs)
        for prj_data in data:
            yield cls(prj_data)

    def get_company(self):
        return company.ACompany(self._data['company']['id'])

    def get_settings(self):
        ws = self.get_workspace()
        if not ws:
            raise Exception('Project has no workspace')
        return settings.get_workspace_settings(ws)

    def get_workspace(self) -> AWorkspace|None:
        ws = self._data['workspace']
        if ws is None:
            return None
        else:
            return AWorkspace(ws['id'])

    @property
    def workspace_id(self):
        return self._data['workspace']['id']

    def set_workspace(self, ws: AWorkspace|str|None) -> bool:
        if ws is None:
            return self.unset_workspace()
        ws_id = ws.id if isinstance(ws, AWorkspace) else ws
        resp = api.track.update_project(self.id, workspace_id=ws_id)
        self.reload()
        return resp

    def unset_workspace(self) -> bool:
        resp = api.track.update_project(self.id, workspace_id=None)
        self.reload()
        return resp

    def get_roots(self):
        # TODO move to different tool
        from agio.core.settings import get_local_settings

        project_settings = get_local_settings(project=self)
        return {k.name: k.path for k in project_settings.get('agio_pipe.local_roots')}
