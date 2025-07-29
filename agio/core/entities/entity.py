from abc import ABC, abstractmethod
from typing import Self, Iterator


class Entity(ABC):
    """
    Base class for database entity
    """
    type_name = None

    def __init__(self, entity: str|dict):
        if isinstance(entity, str):
            # from ID
            self._id = entity
            self._data = self.get_data(entity)
            if not self._data:
                raise Exception(f"No data found for {entity}")
        elif isinstance(entity, dict):
            # from data
            self._id = entity['id']
            self._data = entity
            if set(self._data.keys()) == {'type', 'id'}:
                self.reload()
        else:
            raise TypeError('entity must be a string or dict')

    def reload(self):
        self._data = self.get_data(self.id)

    @classmethod
    def from_data(cls, data: dict) -> 'Entity':
        for cls_ in cls.__subclasses__():
            if cls_.type_name == data.get('type'):
                return cls_(data)

    @property
    def id(self):
        return self._id

    @property
    def data(self):
        return self._data

    @property
    def type(self):
        return self.type_name

    def __str__(self):
        return str(self._id)

    def __repr__(self):
        return f"<{self.__class__.__name__}('{self}')>"

    @classmethod
    @abstractmethod
    def get_data(cls, entity_id: str) -> dict:
        raise NotImplementedError()

    @abstractmethod
    def update(self, **kwargs) -> None:
        raise NotImplementedError()

    @classmethod
    @abstractmethod
    def iter(cls, **kwargs) -> Iterator[Self]:
        raise NotImplementedError()

    @classmethod
    @abstractmethod
    def create(cls, **kwargs) -> Self:
        raise NotImplementedError()

    @abstractmethod
    def delete(self) -> None:
        raise NotImplementedError()

    @classmethod
    @abstractmethod
    def find(cls, **kwargs):
        raise NotImplementedError()

    def serialize(self):
        ...

