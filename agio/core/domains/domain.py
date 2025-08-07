from abc import ABC, abstractmethod
from typing import Self, Iterator


class DomainBase(ABC):
    """
    Base class for database entity
    """
    type_name = None

    def __init__(self, data: str | dict):
        if isinstance(data, str):
            # from ID
            self._data: dict = self.get_data(data)
            if not self._data:
                raise Exception(f"No data found for {data}")
        elif isinstance(data, dict):
            # from data
            self._data: dict = data
            if set(self._data.keys()) == {'type', 'id'}:
                self.reload()
        else:
            raise TypeError('entity must be a string or dict')

    def reload(self):
        self._data = self.get_data(self.id)

    @classmethod
    def from_data(cls, data: dict) -> 'DomainBase':
        for cls_ in cls.__subclasses__():
            if cls_.type_name == data.get('type'):
                return cls_(data)

    @property
    def id(self):
        return self._data['id']

    @property
    def data(self):
        return self._data

    @property
    def type(self):
        return self.type_name

    def __str__(self):
        return str(self.id)

    def __repr__(self):
        return f"<{self.__class__.__name__}('{self}')>"

    @classmethod
    @abstractmethod
    def get_data(cls, object_id: str) -> dict:
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

