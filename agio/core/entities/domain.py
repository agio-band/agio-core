from __future__ import annotations
import json
from abc import ABC, abstractmethod
from typing import Iterator
from uuid import UUID


class DomainBase(ABC):
    """
    Base class for database entity
    """
    domain_name = None

    def __init__(self, data: str | UUID | dict):
        if self.domain_name is None:
            raise AttributeError("Domain name not set")
        if isinstance(data, (str, UUID)):
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
            raise TypeError(f'entity must be a string or dict: {type(data)}')
        fields_data = self._data.get('fields')
        if isinstance(fields_data, str):
            self.data['fields'] = json.loads(fields_data)

    def reload(self):
        self._data = self.get_data(self.id)

    @property
    def id(self):
        return self._data['id']

    @property
    def data(self):
        return self._data

    @property
    def type(self):
        return self.domain_name

    @property
    def name(self):
        return self.data["name"]

    @property
    def code(self):
        return self.data["code"]

    @property
    def fields(self):
        return self._data.get('fields', {})

    def __str__(self):
        return str(self.id)

    def __repr__(self):
        return f"<{self.__class__.__name__}('{self.id}')>"

    def __eq__(self, other):
        return self.id == other.id

    def __hash__(self):
        return hash(self.id)

    @classmethod
    @abstractmethod
    def get_data(cls, object_id: str) -> dict:
        raise NotImplementedError()

    @abstractmethod
    def update(self, **kwargs) -> None:
        raise NotImplementedError()

    @classmethod
    @abstractmethod
    def iter(cls, **kwargs) -> Iterator['DomainBase']:
        raise NotImplementedError()

    @classmethod
    @abstractmethod
    def create(cls, **kwargs) -> 'DomainBase':
        raise NotImplementedError()

    @abstractmethod
    def delete(self) -> None:
        raise NotImplementedError()

    @classmethod
    @abstractmethod
    def find(cls, **kwargs):
        raise NotImplementedError()

    def to_dict(self):
        return self._data

