from __future__ import annotations
from typing import Iterator

from agio.core.domains import DomainBase, AWorkspace
from agio.core import api
from agio.core.domains import project


class ACompany(DomainBase):
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
    def current(cls):
        return cls(api.desk.get_current_company())

    def find_project(self, name: str = None, state: str = None, code: str = None) -> Iterator[project.AProject]:
        kwargs = {'name': name, 'state': state, 'code': code}
        kwargs = {k: v for k, v in kwargs.items() if v is not None}
        yield from project.AProject.find(self.id, **kwargs)

    def workspaces(self) -> Iterator[project.AWorkspace]:
        for item in api.workspace.iter_workspaces(self.id):
            yield AWorkspace(item)