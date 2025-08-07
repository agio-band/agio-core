from typing import Self, Iterator

from agio.core.domains import DomainBase


class ACompany(DomainBase):
    type = "company"

    @classmethod
    def get_data(cls, object_id: str) -> dict:
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
        pass

    ...