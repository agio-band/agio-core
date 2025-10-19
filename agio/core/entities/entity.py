from __future__ import annotations
import json
from functools import cached_property
from typing import Iterator, Generator
from uuid import UUID

from agio.core import api
from agio.core.entities.domain import DomainBase
from typing import TypeVar


class AEntity(DomainBase):
    """
    Provider of project entity
    """
    domain_name = 'entity'
    entity_class = None

    def __init__(self, *args, **kwargs):
        if self.entity_class is None:
            if args and isinstance(args[0], dict) and 'class' in args[0]:
                self.entity_class = args[0]['class']['name']
            else:
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
             class_name: str = None,
             ) -> Iterator[T_Entity]:
        for data in api.track.iter_entities(project_id, class_name or cls.entity_class, parent_id, name):
            yield cls.from_data(data)

    @classmethod
    def create(cls,
               project_id: str|UUID,
               parent_id: str|UUID,
               name: str,
               class_name: str = None,
               fields: dict = None,
               ) -> T_Entity:
        class_name = class_name or cls.entity_class
        if not class_name:
            raise RuntimeError('Entity class name cannot be empty')
        entity_id = api.track.create_entity(
            project_id=project_id,
            parent_id=parent_id,
            entity_class=cls.entity_class,
            name=name,
            fields=fields,
            )
        return cls(entity_id)

    @cached_property
    def fields(self):
        fields_data = self._data.get('fields')
        if not fields_data:
            self.reload()
        fields_data = self._data.get('fields')
        if isinstance(fields_data, dict):
            return fields_data
        elif isinstance(fields_data, str):
            return json.loads(self._data['fields'])
        else:
            raise TypeError('Field data must be a dict or str')

    def delete(self) -> None:
        return api.track.delete_entity(self.id)

    @classmethod
    def find(cls, project_id: str, entity_class: str, entity_name: str) -> T_Entity:
        data = api.track.get_entity_by_name(project_id, entity_class, entity_name)
        if data:
            return cls.from_data(data)

    @classmethod
    def from_data(cls, entity_data) -> T_Entity: # TODO merge from_data and from ID
        entity_id = entity_data.get('id')
        if entity_id is None:
            raise KeyError('Field id is missing')
        entity_class = entity_data.get('class', {}).get('name')
        if entity_class is None:
            entity_data = api.track.get_entity(entity_id)
            entity_class = entity_data.get('class', {}).get('name')
        cls_ = cls.find_entity_class(entity_class)
        if cls_ is None:
            return AEntity(entity_data)
        return cls_(entity_data)

    @classmethod
    def from_id(cls, entity_id: str) -> T_Entity:
        entity_data = api.track.get_entity(entity_id)
        entity_class = entity_data.get('class', {}).get('name')
        cls_ = cls.find_entity_class(entity_class)
        if not cls_:
            return AEntity(entity_data)
        else:
            return cls_(entity_data)

    @property
    def name(self):
        return self._data['name']

    @property
    def id(self):
        return self._data['id']

    @property
    def class_name(self):
        return self._data['class']['name']

    @property
    def class_id(self):
        return self._data['class']['id']

    @property
    def project_id(self):
        return self._data['projectId']

    @cached_property
    def project(self):
        from .project import AProject
        return AProject(self.project_id)

    @classmethod
    def find_entity_class(cls, class_name: str) -> T_Entity:
        for cls_ in AEntity.iter_entity_classes():
            if cls_.entity_class == class_name:
                return cls_

    @classmethod
    def iter_entity_classes(cls) -> Iterator[T_Entity]:
        for _cls in cls.__subclasses__():
            yield _cls

    # schema and hierarchy

    def set_parent(self, parent: T_Entity) -> None:
        ...

    def add_child(self, child: T_Entity) -> None:
        ...

    def _load_parents_data(self, depth: int = 10):
        return api.track.get_entity_hierarchy(self.id, depth, False)

    def get_parents(self) -> Generator[T_Entity|None]:
        items = self._load_parents_data(10)
        if not items:
            return
        for item in items:
            yield self.from_data(item)

    @cached_property
    def hierarchy(self) -> str:
        return '/'.join([x['name'] for x in self._load_parents_data()])

    @cached_property
    def parent(self) -> AEntity|None:
        if self._data.get('parent'):
            return AEntity.from_id(self._data['parent']['id'])

    @property
    def parent_id(self) -> str|None:
        return self._data.get('parentId')

    def _entity_can_be_parent(self, entity: T_Entity) -> bool:
        ...

    def _entity_can_be_child(self, entity: T_Entity) -> bool:
        ...



T_Entity = TypeVar("T_Entity", bound=AEntity)
