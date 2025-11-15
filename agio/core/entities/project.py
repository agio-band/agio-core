from __future__ import annotations
from typing import Iterator
from uuid import UUID

from agio.core import api
from agio.core import settings
from agio.core.entities import domain
from agio.core.entities import workspace as ws
from agio.core.entities import company as company_entity
from agio.core.settings import settings_hub
from agio.core.settings.settings_hub import LocalSettingsHub


class AProject(domain.DomainBase):
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
    def iter(cls, company_id: str|UUID, **kwargs) -> Iterator['AProject']:
        for prj_data in api.track.iter_projects(company_id=company_id, **kwargs):
            yield cls(prj_data)

    @classmethod
    def create(cls, **kwargs) -> 'AProject':
        raise NotImplementedError()

    def delete(self) -> None:
        raise NotImplementedError()

    @classmethod
    def find(cls, name: str = None, code: str = None, state: str = None,
        company: company_entity.ACompany|str = None) -> 'AProject':
        if isinstance(company, company_entity.ACompany):
            company_id = company.id
        elif isinstance(company, (str, UUID)):
            company_id = str(company)
        elif company is None:
            comp = company_entity.ACompany.current()
            if not comp:
                raise Exception(f"Company not provided or not found")
            company_id = comp.id
        else:
            raise TypeError("Invalid type for project_company")
        data = api.track.find_project(company_id, name=name, code=code, state=state)
        if data is not None:
            return cls(data)


    def get_company(self):
        return company_entity.ACompany(self._data['company']['id'])

    @property
    def company(self):
        return self.get_company()

    @property
    def workspace(self):
        return self.get_workspace()

    def get_workspace(self) -> ws.AWorkspace|None:
        workspace_dict = self._data['workspace']
        if workspace_dict is None:
            return None
        else:
            return ws.AWorkspace(workspace_dict['id'])

    @property
    def workspace_id(self):
        return self._data['workspace']['id'] if self._data['workspace'] else None

    @property
    def revision_id(self):
        return self._data['workspaceRevision']['id'] if self._data['workspaceRevision'] else None

    @property
    def workspace_launching_id(self):
        return self.revision_id or self.workspace_id

    def set_workspace(self, workspace: ws.AWorkspace|str|None) -> bool:
        if workspace is None:
            return self.unset_workspace()
        ws_id = workspace.id if isinstance(workspace, ws.AWorkspace) else workspace
        resp = api.track.update_project(self.id, workspace_id=ws_id)
        self.reload()
        return resp

    def unset_workspace(self) -> bool:
        resp = api.track.update_project(self.id, workspace_id=None)
        self.reload()
        return resp

    def set_revision(self, revision: str|None) -> bool:
        raise NotImplementedError()

    def unset_revision(self) -> bool:
        raise NotImplementedError()

    def get_roots(self):
        project_settings = self.get_local_settings()
        return {k.name: k.path for k in project_settings.get('agio_pipe.local_roots')}

    @property
    def mount_root(self):
        roots = self.get_roots()
        if 'projects' not in roots: # todo: is static root name?
            raise ValueError(f'Local settings has no "projects" root parameter for project {self.name} ({self.id})')
        local_storage_root = roots['projects']
        company_root = f'{local_storage_root}/{self.get_company().code}'
        return company_root

    # settings
    def get_settings(self):
        """Return remote pipeline settings for current project"""
        return self.get_workspace().get_settings(self.revision_id)

    def get_local_settings(self) -> LocalSettingsHub:
        """Return local settings for current project"""
        return settings.get_local_settings(self)

    def set_local_settings(self, settings_data: settings_hub.LocalSettingsHub | dict):
        """Save local settings for current project"""
        if isinstance(settings_data, dict):
            settings_data = settings_hub.LocalSettingsHub(settings_data)
        return settings.save_local_settings(settings_data, self)

