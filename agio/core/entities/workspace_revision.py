from __future__ import annotations

from typing import Iterator

from agio.core import api
from agio.core.api.utils import NOTSET
from agio.core.entities import workspace
from agio.core.settings import settings_hub
from . import APackageRelease
from .base_object import BaseObject
from .workspace_settings import AWorkspaceSettings


class AWorkspaceRevision(BaseObject):
    object_name = 'workspace_revision'

    @classmethod
    def get_data(cls, object_id: str, client=None) -> dict:
        return api.workspace.get_revision(object_id, client=client)

    def update(self,
               set_current: bool = NOTSET,
               layout: dict = NOTSET,
               status: str = NOTSET,
               ) -> None:
        api.workspace.update_revision(self.id, set_current=set_current, layout=layout, status=status, client=self.client)

    @classmethod
    def iter(cls, workspace_id: str, client=None, **kwargs) -> Iterator['AWorkspaceRevision']:
        for data in api.workspace.iter_revisions(workspace_id, client=client):
            yield cls(data, client=client)

    @classmethod
    def create(cls,
               workspace_id: str|workspace.AWorkspace,
               package_releases: list,
               set_current: bool = NOTSET,
               status: str = NOTSET,
               layout: dict = NOTSET,
               comment: str = NOTSET,
               metadata: dict = NOTSET,
               client=None,
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
            metadata=metadata or {},
            client=client,
        )
        return cls(revision_id, client=client)

    def delete(self) -> None:
        api.workspace.delete_revision(self.id, client=self.client)

    @classmethod
    def find(cls,
             workspace_id: str = NOTSET,
             is_current: bool = NOTSET,
             ready_only: bool = NOTSET,
             client=None,
             ) -> AWorkspaceRevision|None:
        data = api.workspace.find_revision(
            workspace_id=workspace_id,
            is_ready=ready_only,
            is_current=is_current,
            client=client,
        )
        if data:
            return cls(data, client=client)

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
            self._data["_settings_data"] = api.workspace.get_settings_by_revision_id(self.id, client=self.client)['data']
        return self._data["_settings_data"]

    def get_settings(self):
        data = self.get_settings_data()
        return settings_hub.WorkspaceSettingsHub(data)

    def copy_settings_from(self, source: str|AWorkspaceRevision):
        if isinstance(source, str):
            source = AWorkspaceRevision(source)
        settings = source.get_settings()
        return self.set_settings(settings.dump(skip_default=True), False)

    def get_package_list(self):
        for pkg_data in self._data.get("packageReleases"):
            yield APackageRelease(pkg_data)

    def get_manager(self):
        from agio.core.workspaces import AWorkspaceManager

        return AWorkspaceManager(self)

    def set_layout(self, layout: dict):
        return api.workspace.update_revision(
            revision_id=self.id,
            layout=layout,
            client=self.client,
        )

    def set_settings(self, settings_data: dict|settings_hub.WorkspaceSettingsHub, set_current: bool = True) -> str:
        if not isinstance(settings_data, dict):
            settings_data = settings_data.dump()
        settings = AWorkspaceSettings.create(self.id, settings_data, set_current=set_current)
        return settings.id

    def set_current(self, is_current: bool):
        return api.workspace.update_revision(self.id, set_current=is_current, client=self.client)

    def get_settings_id(self):
        settings_data = api.workspace.get_settings_by_revision_id(self.id, client=self.client)
        if settings_data:
            return settings_data['id']
        return None

    @classmethod
    def get_from_settings_id(cls, settings_id: str, client=None):
        data = api.workspace.get_revision_by_settings_id(settings_id, client=client)
        return cls(data, client=client)