from __future__ import annotations
from functools import cached_property
from typing import TYPE_CHECKING

from agio.core import api
if TYPE_CHECKING:
    from agio.core.entities import AEntity


class EntityRelationMixin:
    @property
    def entity_id(self) -> str|None:
        return self._data.get("entityId")

    @cached_property
    def entity(self) -> AEntity|None:
        from agio.core.entities import AEntity
        if self.entity_id:
            entity_data = api.track.get_entity(self.entity_id, client=self.client)
            return AEntity.from_data(entity_data)
        return None
