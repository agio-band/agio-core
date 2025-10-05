from __future__ import annotations
import json
from functools import cached_property
from typing import Iterator
from uuid import UUID

from agio.core import api
from agio.core.domains.domain import DomainBase


class AEntity(DomainBase):
    """
    Provider of project entity
    """
    domain_name = 'entity'
    entity_class = None

    def __init__(self, *args, **kwargs):
        if self.entity_class is None:
            raise RuntimeError('Entity class is not defined')
        super().__init__(*args, **kwargs)
        if self._data['class']['name'] != self.entity_class:
            raise RuntimeError('Entity class name does not match attribute "entity_class"')

    @classmethod
    def get_data(cls, object_id: str) -> dict:
        return api.track.get_entity(object_id)

    def update(self, name: str, fields: dict) -> None:
        if api.track.update_entity(self.id, name, fields):
            self.reload()

    @classmethod
    def iter(cls,
             project_id: str|UUID,
             parent_id: str|UUID,
             name: str = None, # can be regex
             ) -> Iterator['AEntity']:
        for data in api.track.iter_entities(project_id, cls.entity_class, parent_id, name):
            yield cls.from_data(data)

    @classmethod
    def create(cls,
               project_id: str|UUID,
               entity_id: str|UUID,
               name: str,
               fields: dict = None,
               ) -> 'AEntity':
        entity_id = api.track.create_entity(
            project_id=project_id,
            parent_id=entity_id,
            entity_class=cls.entity_class,
            name=name,
            fields=fields,
            )
        return cls(entity_id)

    @cached_property
    def fields(self):
        return json.loads(self._data['fields'])

    def delete(self) -> None:
        return api.track.delete_entity(self.id)

    @classmethod
    def find(cls, project_id: str, entity_class: str, entity_name: str) -> 'AEntity':
        data = api.track.get_entity_by_name(project_id, entity_class, entity_name)
        if data:
            return cls.from_data(data)

    @classmethod
    def from_data(cls, entity_data) -> type['AEntity']: # TODO merge from_data and from ID
        entity_id = entity_data.get('id')
        if entity_id is None:
            raise KeyError('Field id is missing')
        entity_class = entity_data.get('class', {}).get('name')
        if entity_class is None:
            entity_data = api.track.get_entity(entity_id)
            entity_class = entity_data.get('class', {}).get('name')
        cls_ = cls.find_entity_class(entity_class)
        if cls_ is None:
            raise KeyError('Entity class {} not found'.format(entity_class))
        return cls_(entity_data)

    @classmethod
    def from_id(cls, entity_id: str) -> 'AEntity':
        entity_data = api.track.get_entity(entity_id)
        entity_class = entity_data.get('class', {}).get('name')
        cls_ = cls.find_entity_class(entity_class)
        if cls_ is None:
            raise KeyError('Entity class {} not found'.format(entity_class))
        return cls_(entity_data)

    @property
    def name(self):
        return self._data['name']

    @property
    def id(self):
        return self._data['id']

    @property
    def project_id(self):
        return self._data['projectId']

    @cached_property
    def project(self):
        from .project import AProject
        return AProject(self.project_id)

    @classmethod
    def find_entity_class(cls, class_name: str) -> type['AEntity']:
        for cls_ in AEntity.iter_entity_classes():
            if cls_.entity_class == class_name:
                return cls_

    @classmethod
    def iter_entity_classes(cls) -> Iterator[type['AEntity']]:
        for _cls in cls.__subclasses__():
            yield _cls

    # schema and hierarchy

    def set_parent(self, parent: 'AEntity') -> None:
        ...

    def add_child(self, child: 'AEntity') -> None:
        ...

    def _entity_can_be_parent(self, entity: type['AEntity']) -> bool:
        ...

    def _entity_can_be_child(self, entity: type['AEntity']) -> bool:
        ...

