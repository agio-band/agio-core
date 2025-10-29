from __future__ import annotations
from typing import Iterator

from agio.core import api
from agio.core.api.utils import NOTSET
from agio.core.entities import workspace
from . import APackageRelease
from .entity import DomainBase



class AWorkspaceRevision(DomainBase):
    domain_name = 'workspace_revision'

    @classmethod
    def get_data(cls, object_id: str) -> dict:
        return api.workspace.get_revision(object_id)

    def update(self,
               set_current: bool = NOTSET,
               layout: dict = NOTSET,
               status: str = NOTSET,
               ) -> None:
        api.workspace.update_revision(self.id, set_current=set_current, layout=layout, status=status)

    @classmethod
    def iter(cls, workspace_id: str, **kwargs) -> Iterator['AWorkspaceRevision']:
        for data in api.workspace.iter_revisions(workspace_id):
            yield cls(**data)

    @classmethod
    def create(cls,
               workspace_id: str|workspace.AWorkspace,
               package_releases: list,
               set_current: bool = NOTSET,
               status: str = NOTSET,
               layout: dict = NOTSET,
               comment: str = NOTSET,
               metadata: dict = NOTSET,
               ) -> 'AWorkspaceRevision':
        release_ids = []
        for package_release in package_releases:
            if isinstance(package_release, str):
                release_ids.append(package_release)
            elif isinstance(package_release, APackageRelease):
                release_ids.append(package_release.id)
            elif isinstance(package_release, dict):
                release_ids.append(package_release["id"])
            else:
                raise TypeError(f"Invalid package_release type: {type(package_release)}")
        if isinstance(workspace_id, workspace.AWorkspace):
            workspace_id = workspace_id.id
        revision_id = api.workspace.create_revision(
            workspace_id=workspace_id,
            package_release_ids=release_ids,
            set_current=set_current,
            status=status or 'ready', # TODO
            layout=layout or NOTSET,
            comment=comment or NOTSET,
            metadata=metadata or {}
        )
        return cls(revision_id)

    def delete(self) -> None:
        api.workspace.delete_revision(self.id)

    @classmethod
    def find(cls,
             workspace_id: str = NOTSET,
             is_current: bool = NOTSET,
             ready_only: bool = NOTSET,
             ) -> 'AWorkspaceRevision':
        data = api.workspace.find_revision(
            workspace_id=workspace_id,
            is_ready=ready_only,
            is_current=is_current,
        )
        if data:
            return cls(data)

    @property
    def metadata(self):
        return self._data.get("metadata", {})

    @property
    def workspace_id(self):
        return self._data['workspaceId']

    def get_workspace(self):
        from agio.core.entities import AWorkspace

        return AWorkspace(self.workspace_id)

    def get_comment(self):
        return self._data.get("comment")

    def get_layout(self):
        return self._data.get("layout")

    def get_settings_data(self) -> dict:
        """
        Return raw dict settings data
        """
        if '_settings_data' not in self._data:
            self._data["_settings_data"] = api.workspace.get_settings_by_revision_id(self.id)['data']
        return self._data["_settings_data"]

    def get_package_list(self):
        for pkg_data in self._data.get("packageReleases"):
            yield APackageRelease(pkg_data)

    def get_manager(self):
        from agio.core.pkg import AWorkspaceManager

        return AWorkspaceManager(self)

    def set_layout(self, layout: dict):
        return api.workspace.update_revision(
            revision_id=self.id,
            layout=layout
        )

    def set_settings_data(self, settings_data: dict, set_current: bool = True) -> str:
        return api.workspace.create_revision_settings(
            self.id,
            settings_data,
            set_current=set_current
        )

    def set_current(self, is_current: bool):
        return api.workspace.update_revision(self.id, set_current=is_current)
