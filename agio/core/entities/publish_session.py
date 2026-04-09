from __future__ import annotations

from typing import Iterator
from uuid import UUID

from agio.core.api import pipe
from agio.core.entities import BaseObject, AWorkspace, AEntity
from agio.core.entities.project import AProject


class APublishSession(BaseObject):
    object_name = "publish_session"

    @classmethod
    def get_data(cls, object_id: str) -> dict:
        return pipe.get_publish_session(object_id)

    def update(self,
               state: str = None,
               status: str = None,
               comment: str = None,
               data: dict = None
               ) -> None:
        to_update = {}
        if state is not None:
            to_update["state"] = state
        if status is not None:
            to_update["status"] = status
        if comment is not None:
            to_update["comment"] = comment
        if data is not None:
            to_update["data"] = data
        pipe.update_publish_session(self.id, **to_update)
        self.reload()

    @classmethod
    def iter(cls, project_id: str|UUID, items_per_page: int = 25) -> Iterator[APublishSession]:
        yield from (cls(data) for data in pipe.iter_publish_sessions(project_id, items_per_page=items_per_page))

    @classmethod
    def create(cls,
               entity_id: str | UUID,
               name: str,
               version: int,
               state: str = None,
               status: str = None,
               workspace_settings_id: str = None,
               comment: str = None,
               data: dict = None) -> APublishSession:
        session_id = pipe.create_publish_session(
            entity_id,
            name=name,
            version=version,
            state=state,
            status=status,
            comment=comment,
            workspace_settings_id=workspace_settings_id or cls._get_current_settings_workspace_id(entity_id),
            data=data
        )
        return cls(pipe.get_publish_session(session_id))

    @classmethod
    def _get_current_settings_workspace_id(cls, entity_id: str|None):
        if entity_id:
            project: AProject = AEntity.from_id(entity_id).project
            ws = project.get_workspace()
        else:
            ws = AWorkspace.current()
        settings_id = ws.get_current_revision().get_settings_id()
        if not settings_id:
            raise Exception(f'No settings found for current workspace {ws}')
        return settings_id

    @classmethod
    def get_next_version(cls, entity_id: str|UUID) -> int:
        return pipe.get_next_session_version(entity_id)

    def delete(self) -> None:
        pass

    @classmethod
    def find(cls, **kwargs):
        pass

