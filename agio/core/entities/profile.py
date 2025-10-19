from __future__ import annotations
from typing import Iterator
from agio.core import api
from agio.core.entities import DomainBase


class AProfile(DomainBase):
    domain_name = "profile"

    @classmethod
    def get_data(cls, object_id: str) -> dict:
        return api.profile.get_user_by_id(object_id)

    def update(self, **kwargs) -> None:
        raise NotImplementedError()

    @classmethod
    def iter(cls, **kwargs) -> Iterator['AProfile']:
        raise NotImplementedError()

    @classmethod
    def create(cls, **kwargs) -> 'AProfile':
        raise NotImplementedError()

    def delete(self) -> None:
        raise NotImplementedError()

    @classmethod
    def find(cls, **kwargs):
        raise NotImplementedError()

    @classmethod
    def current(cls, **kwargs) -> 'AProfile':
        data = api.profile.get_current_user()
        if not data:
            raise Exception('Not found')
        return cls(data)

    @property
    def first_name(self):
        return self.data['firstName']

    @property
    def last_name(self):
        return self.data['lastName']

    @property
    def email(self):
        return self.data['email']

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"