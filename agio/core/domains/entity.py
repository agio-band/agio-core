from functools import cached_property
from typing import Self, Iterator

from agio.core import api
from agio.core.domains.domain import DomainBase


class AEntity(DomainBase):
    """
    Provider of project entity
    """
    entity_class = None
    def __init__(self, *args, **kwargs):
        if self.entity_class is None:
            raise RuntimeError('Entity class is not defined')
        super().__init__(*args, **kwargs)
        if self._data['class']['name'] != self.entity_class:
            raise RuntimeError('Entity class does not match entity class')

    @classmethod
    def get_data(cls, entity_id: str) -> dict:
        return api.track.get_entity(entity_id)

    def update(self, **kwargs) -> None:
        raise NotImplementedError('Should be implemented in subclass')

    @classmethod
    def iter(cls, **kwargs) -> Iterator[Self]:
        pass

    @classmethod
    def create(cls, **kwargs) -> Self:
        pass

    def delete(self) -> None:
        pass

    @classmethod
    def find(cls, project_id: str, entity_class: str, entity_name: str) -> Self:
        return api.track.get_entity_by_name(project_id, entity_class, entity_name)

    @classmethod
    def from_data(cls, entity_data) -> type[Self]:
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

    @property
    def project_id(self):
        return self._data['projectId']

    @cached_property
    def project(self):
        from .project import AProject
        return AProject(self.project_id)

    @classmethod
    def find_entity_class(cls, class_name: str) -> type[Self]:
        for cls_ in cls.iter_entity_classes():
            if cls_.entity_class == class_name:
                return cls_

    @classmethod
    def iter_entity_classes(cls) -> Iterator[type[Self]]:
        for _cls in cls.__subclasses__():
            yield _cls

    # schema and hierarchy

    def set_parent(self, parent: Self) -> None:
        ...

    def add_child(self, child: Self) -> None:
        ...

    def _entity_can_be_parent(self, entity: type[Self]) -> bool:
        ...

    def _entity_can_be_child(self, entity: type[Self]) -> bool:
        ...

