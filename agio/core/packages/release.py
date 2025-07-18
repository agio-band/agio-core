from typing import Self, Iterator

from agio.core.api.utils import NOTSET
from agio.core.entities import Entity
from agio.core import api


class APackageRelease(Entity):
    @classmethod
    def get_data(cls, entity_id: str) -> dict:
        return api.package.get_package_release(entity_id)

    def update(self,
               label: str = NOTSET,
               description: str = NOTSET,
               assets: dict = NOTSET,
               metadata: dict = NOTSET,
               ) -> None:
        resp = api.package.update_package_release(
            self.id,
            label=label,
            description=description,
            assets=assets,
            metadata=metadata,
        )
        self._data.update(resp)

    @classmethod
    def iter(cls, package_id: str) -> Iterator[Self]:
        for release_data in api.package.iter_package_releases(package_id):
            yield cls(release_data)

    @classmethod
    def create(cls,
               package_id: str,
               version: str,
               assets: dict,
               label: str,
               description: str = NOTSET,
               metadata: dict = NOTSET,
               ) -> Self:
        release_id = api.package.create_package_release(
            package_id=package_id,
            version=version,
            assets=assets,
            label=label,
            description=description,
            metadata=metadata or {},
        )
        return cls(release_id)

    def delete(self) -> bool:
        return api.package.delete_package_release(self.id)

    @classmethod
    def find(cls, package_name: str, version: str) -> Self|None:
        data = api.package.get_package_release_by_name_and_version(package_name, version)
        if data:
            return cls(data)

    def get_package_id(self) -> str:
        return self._data['packageId']

    def get_package(self):
        from .package import APackage
        return APackage(self._data.get('packageId'))

    def get_assets(self):
        return self._data.get('assets')

    def get_version(self):
        return self._data.get('name')