from typing import Self, Iterator

from agio.core.domains import DomainBase


class AProductType(DomainBase):

    def __init__(self, data: str) -> None:
        pass

    @property
    def name(self):
        return 'workfile'

    @classmethod
    def get_data(cls, entity_id: str) -> dict:
        pass

    def update(self, **kwargs) -> None:
        pass

    @classmethod
    def iter(cls, **kwargs) -> Iterator[Self]:
        pass

    @classmethod
    def create(cls, **kwargs) -> Self:
        pass

    def delete(self) -> None:
        pass

    @classmethod
    def find(cls, **kwargs):
        return