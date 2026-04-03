from functools import cached_property

from agio.core.entities import entity, project


class ATask(entity.AEntity):
    entity_class = "Task"

    @property
    def entity_id(self) -> str:
        return self._data["parent"]["id"]

    @property
    def entity_type(self) -> str:
        return self._data['parent']['class']['name']

    @cached_property
    def entity(self) -> entity.AEntity:
        return entity.AEntity.from_id(self._data['parent']['id'])

    @cached_property
    def project(self):
        return project.AProject(self._data['projectId'])
