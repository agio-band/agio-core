from __future__ import annotations
from typing import Iterator

from agio.core.entities import workspace as ws, domain as dm
from agio.core import api
from agio.core.entities import project
from agio.core.exceptions import NotFoundError


class ACompany(dm.DomainBase):
    domain_name = "company"

    @classmethod
    def get_data(cls, object_id: str) -> dict:
        return api.desk.get_company(object_id)

    def update(self, **kwargs) -> None:
        raise NotImplementedError()

    @classmethod
    def iter(cls, **kwargs) -> Iterator['ACompany']:
        yield from api.desk.iter_companies(**kwargs)

    @classmethod
    def create(cls, **kwargs) -> ACompany:
        raise NotImplementedError()

    def delete(self) -> None:
        raise NotImplementedError()

    @classmethod
    def find(cls, **kwargs):
        raise NotImplementedError()

    @classmethod
    def get_by_name(cls, name: str) -> ACompany|None:
        try:
            data = api.desk.get_company_by_code(name)
            return ACompany(data)
        except NotFoundError:
            return None

    @classmethod
    def current(cls):
        return cls(api.desk.get_current_company())

    @classmethod
    def switch(cls, company_id: str) -> ACompany:
        if api.desk.switch_company(company_id):
            return cls.current()
        else:
            raise NotFoundError(detail="Company not found")

    def find_project(self, name: str = None, state: str = None, code: str = None) -> project.AProject|None:
        return project.AProject.find(company=self.id, name=name, state=state, code=code)

    def iter_projects(self, **kwargs) -> Iterator[project.AProject]:
        raise NotImplementedError()

    def workspaces(self) -> Iterator[ws.AWorkspace]:
        for item in api.workspace.iter_workspaces(self.id):
            yield ws.AWorkspace(item)