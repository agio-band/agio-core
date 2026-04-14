from __future__ import annotations
from typing import Iterator

from agio.core.entities import workspace as ws, base_object as base
from agio.core import api
from agio.core.entities import project
from agio.core.exceptions import NotFoundError


class ACompany(base.BaseObject):
    object_name = "company"

    @classmethod
    def get_data(cls, object_id: str, client=None) -> dict:
        return api.desk.get_company(object_id, client=client)

    def update(self, **kwargs) -> None:
        raise NotImplementedError()

    @classmethod
    def iter(cls, client=None, **kwargs) -> Iterator[ACompany]:
        yield from (cls(data, client=client) for data in api.desk.iter_companies(**kwargs, client=client))

    @classmethod
    def create(cls, **kwargs) -> ACompany:
        raise NotImplementedError()

    def delete(self) -> None:
        raise NotImplementedError()

    @classmethod
    def find(cls, **kwargs):
        raise NotImplementedError()

    @classmethod
    def get_by_name(cls, name: str, client=None) -> ACompany|None:
        try:
            data = api.desk.get_company_by_code(name, client=client)
            return cls(data, client=client)
        except NotFoundError:
            return None

    @classmethod
    def current(cls, client=None):
        return cls(api.desk.get_current_company(client=client), client=client)

    @classmethod
    def switch(cls, company_id: str, client=None) -> ACompany:
        """Deprecated"""
        if api.desk.switch_company(company_id, client=client):
            return cls.current(client=client)
        else:
            raise NotFoundError(detail="Company not found")

    @property
    def host_user(self):
        return self._data.get('hostUser') or {}

    def find_project(self, name: str = None, state: str = None, code: str = None) -> project.AProject|None:
        return project.AProject.find(company=self.id, name=name, state=state, code=code)

    def iter_projects(self, **kwargs) -> Iterator[project.AProject]:
        raise NotImplementedError()

    def workspaces(self) -> Iterator[ws.AWorkspace]:
        for item in api.workspace.iter_workspaces(company_id=self.id, client=self.client):
            yield ws.AWorkspace(item, client=self.client)