from typing import Iterator, Self

from agio.core import api
from agio.core.api.utils import NOTSET
from . import APackageRelease
from .entity import DomainBase
from .package import APackage


class AWorkspaceRevision(DomainBase):
    type_name = 'workspace_revision'

    @classmethod
    def get_data(cls, object_id: str) -> dict:
        return api.workspace.get_revision(object_id)

    def update(self,
               set_current: bool = NOTSET,
               layout: dict = NOTSET,
               status: str = NOTSET,
               ) -> None:
        api.workspace.update_revision(set_current=set_current, layout=layout, status=status)

    @classmethod
    def iter(cls, workspace_id: str, **kwargs) -> Iterator[Self]:
        for data in api.workspace.iter_revisions(workspace_id):
            yield cls(**data)

    @classmethod
    def create(cls,
               workspace_id: str,
               package_releases: list,
               set_current: bool = NOTSET,
               status: str = NOTSET,
               layout: dict = NOTSET,
               comment: str = NOTSET,
               ) -> Self:
        release_ids = []
        for package_release in package_releases:
            if isinstance(package_release, str):
                release_ids.append(package_release)
            elif isinstance(package_release, APackage):
                release_ids.append(package_release.id)
            elif isinstance(package_release, dict):
                release_ids.append(package_release["id"])
            else:
                raise TypeError(f"Invalid package_release type: {type(package_release)}")
        revision_id = api.workspace.create_revision(
            workspace_id=workspace_id,
            package_release_ids=release_ids,
            set_current=set_current,
            status=status,
            layout=layout,
            comment=comment,
        )
        return cls(revision_id)

    def delete(self) -> None:
        api.workspace.delete_revision(self.id)

    @classmethod
    def find(cls,
             workspace_id: str = NOTSET,
             workspace_name: str = NOTSET,
             is_current: bool = NOTSET,
             ready_only: bool = NOTSET,
             ) -> Self:
        data = api.workspace.find_revision(
            workspace_id=workspace_id,
            workspace_name=workspace_name,
            ready_only=ready_only,
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

    def get_comment(self):
        return self._data.get("comment")

    def get_layout(self):
        return self._data.get("layout")

    def get_settings(self):
        return self._data.get("settings")

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

    def set_settings(self, settings_data: dict) -> str:
        return api.workspace.create_revision_settings(
            self.id,
            settings_data,
            set_current=True
        )

    def set_current(self, is_current: bool):
        return api.workspace.update_revision(self.id, set_current=is_current)
