from __future__ import annotations

import os
from typing import Iterator

from agio.core import api
from ...tools import env_names
from agio.core.api.utils import NOTSET
from . import APackageRelease, APackage
from .entity import DomainBase
from .workspace_revision import AWorkspaceRevision
from ..events import emit
from ..exceptions import RequestError, SettingsRevisionNotExists, WorkspaceNotDefined
from ..settings import settings_hub


class AWorkspace(DomainBase):
    domain_name = 'workspace'

    @classmethod
    def get_data(cls, object_id: str) -> dict:
        return api.workspace.get_workspace(object_id)

    def update(self, name: str = NOTSET, description: str = None) -> None:
        if api.workspace.update_workspace(
            self.id,
            name=name,
            description=description,
        ):
            self.reload()

    @classmethod
    def iter(cls, company_id: str = None) -> Iterator['AWorkspace']:
        company_id = company_id or api.desk.get_current_company()['id']
        for data in api.workspace.iter_workspaces(company_id=company_id):
            yield cls(data)

    @classmethod
    def create(cls, company_id: str, name: str, description: str = NOTSET) -> 'AWorkspace':
        ws_id = api.workspace.create_workspace(
            company_id=company_id,
            name=name,
            description=description,
        )
        return cls(ws_id)

    @classmethod
    def from_revision_id(cls, revision_id: str) -> 'AWorkspace':
        rev = AWorkspaceRevision(revision_id)
        return rev.get_workspace()

    def delete(self) -> bool:
        return api.workspace.delete_workspace(self.id)

    def is_deleted(self):
        if 'deletedAt' not in self._data:
            raise ValueError('Data is missing "deletedAt"')
        return bool(self._data['deletedAt'])

    @classmethod
    def find(cls, company_id: str = None, name: str = NOTSET) -> 'AWorkspace':
        company_id = company_id or api.desk.get_current_company()['id']
        data = api.workspace.find_workspace(company_id=company_id, name=name)
        if data:
            return cls(data)

    @classmethod
    def current(cls):
        ws_id = os.getenv(env_names.WORKSPACE_ID)
        if not ws_id:
            raise WorkspaceNotDefined
        return cls(ws_id)

    def get_current_revision(self):
        revision = api.workspace.get_revision_by_workspace_id(self.id)
        return AWorkspaceRevision(revision)

    def get_manager(self):
        from agio.core.workspaces import AWorkspaceManager

        revision_id = os.getenv(env_names.REVISION_ID)
        if revision_id:
            revision = AWorkspaceRevision(revision_id)
        else:
            revision = self.get_current_revision()
        return AWorkspaceManager(revision)

    @property
    def company_id(self):
        return self._data['company']['id']

    def get_company(self):
        from .company import ACompany

        return ACompany(self.company_id)

    def _find_release(self, input_data: dict|str|APackageRelease|APackage) -> APackageRelease:
        if isinstance(input_data, APackageRelease):
            return input_data
        elif isinstance(input_data, APackage):
            latest_release = input_data.latest_release()
            if not latest_release:
                raise Exception(f'Release for package {input_data} not found')
            return latest_release
        elif isinstance(input_data, str):

            try:
                release = api.package.get_package_release(input_data)
                return APackageRelease(release)
            except RequestError:
                try:
                    pkg = APackage.find(name=input_data)
                    return pkg.latest_release()
                except RequestError:
                    raise Exception(f'Package or release {input_data} not found')
        elif isinstance(input_data, dict):
            release = api.package.get_package_release_by_name_and_version(
                package_name=input_data['name'],
                version=input_data['version'],
            )
            if not release:
                raise Exception(f'Package release {input_data} not found')
            return APackageRelease(release)
        else:
            raise Exception(f'Unknown input type {type(input_data)}')

    def _find_revision(self, revision_id: str) -> AWorkspaceRevision|None:
        data = api.workspace.find_workspace_revision(workspace_id=self.id, revision_id=revision_id)
        if data:
            return AWorkspaceRevision(data)

    def set_package_list(
            self,
            packages: list[dict|str],
            set_current: bool = False,
            comment: str = None,
            layout: dict = None,
    ):
        if not packages:
            raise Exception(f'No packages to set')
        # collect releases
        releases: list[APackageRelease] = [self._find_release(p) for p in packages]
        if not releases:
            raise Exception(f'No package releases found')
        pkg_names = [p.get_package_name() for p in releases]
        for pkg_name in pkg_names:
            if pkg_names.count(pkg_name)>1:
                raise Exception(f'Multiple packages with same name: {pkg_name}')
        names = [rel.get_package_name() for rel in releases]
        # check core package exists
        if 'agio_core' not in names:
            raise Exception(f'agio-core package is required but not added')
        release_ids = [rel.id for rel in releases]
        # create revision
        result = api.workspace.create_revision(
            workspace_id=self.id,
            package_release_ids=release_ids,
            set_current=set_current,
            status='ready', # TODO change to "sync"
            comment=comment,
            layout=layout or NOTSET,
        )
        return AWorkspaceRevision(result)

    def get_settings(self, revision_id: str = None) -> settings_hub.WorkspaceSettingsHub:
        try:
            if revision_id:
                revision = self._find_revision(revision_id)
            else:
                revision = self.get_current_revision()
            settings_data = revision.get_settings_data()
        except SettingsRevisionNotExists:
            settings_data = {}
            revision = None
        # create workspace settings instance with applied values
        settings = settings_hub.WorkspaceSettingsHub(settings_data)
        emit('core.settings.workspace_settings_loaded',
             {'settings': settings, 'workspace': self, 'revision': revision})
        return settings

    def set_settings(self, settings: dict | settings_hub.WorkspaceSettingsHub, set_current: bool = True):
        rev = self.get_current_revision()
        if not isinstance(settings, dict):
            settings = settings.dump()
        emit('core.settings.before_workspace_settings_save',
             {'settings': settings, 'workspace': self, 'revision': rev})
        rev.set_settings_data(settings, set_current=set_current)
        emit('core.settings.workspace_settings_saved',
             {'settings': settings, 'workspace': self, 'revision': rev})
