from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import Iterator
from uuid import UUID

from agio.tools import modules


class BaseObject(ABC):
    """
    Base class for database entity
    """
    object_name = None

    def __init__(self, data: str | UUID | dict):
        if self.object_name is None:
            raise AttributeError(f"object_name not set for {self.__class__.__name__}")
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
        return self.object_name

    @property
    def name(self):
        return self.data.get("name")

    @property
    def code(self):
        return self.data.get("code")

    @property
    def fields(self):
        return self._data.get('fields', {})

    def set_fields(self, **kwargs) -> None:
        fields = self.fields.copy()
        fields.update(kwargs)
        self.update(fields=kwargs)
        self.reload()

    def __str__(self):
        return str(self.id)

    def __repr__(self):
        name = self.code or self.name or ''
        return f"<{self.__class__.__name__} {name} ('{self.id}')>"

    def __eq__(self, other):
        if not isinstance(other, BaseObject):
            raise TypeError(f"Cannot compare with {type(other)}")
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
    def iter(cls, **kwargs) -> Iterator['BaseObject']:
        raise NotImplementedError()

    @classmethod
    @abstractmethod
    def create(cls, **kwargs) -> 'BaseObject':
        raise NotImplementedError()

    @abstractmethod
    def delete(self) -> None:
        raise NotImplementedError()

    @classmethod
    @abstractmethod
    def find(cls, **kwargs):
        raise NotImplementedError()

    def to_dict(self) -> dict:
        return self._data

    def serialize(self) -> dict:
        data = self.to_dict()
        data['_'] = modules.get_object_dot_path(self.__class__)
        return data

    @classmethod
    def deserialize(cls, entity_data: dict):
        class_dotted_path = entity_data.pop('_')
        _cls = modules.import_object_by_dotted_path(class_dotted_path)
        return _cls(entity_data)
