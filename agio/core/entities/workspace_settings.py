from __future__ import annotations

from typing import Iterator

from agio.core import api
from agio.core.entities import BaseObject


class AWorkspaceSettings(BaseObject):
    object_name = 'workspace_settings'

    @classmethod
    def get_data(cls, object_id: str) -> dict:
        return api.workspace.get_revision_settings(object_id)

    def update(self, is_current: bool = None, comment: str = None) -> bool:
        return api.workspace.update_revision_settings(self.id, is_current=is_current, comment=comment)

    def set_current(self):
        return self.update(is_current=True)

    @classmethod
    def iter(cls, **kwargs) -> Iterator[AWorkspaceSettings]:
        raise NotImplementedError

    @classmethod
    def create(cls, revision_id, settings_data: dict, set_current: bool = False, **kwargs) -> AWorkspaceSettings:
        settings_id = api.workspace.create_revision_settings(
            revision_id,
            settings_data,
            set_current=set_current
        )
        return cls(settings_id)

    def delete(self) -> None:
        pass


    @classmethod
    def find(cls, **kwargs):
        pass