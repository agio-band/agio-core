from __future__ import annotations
import logging
from typing import Generator

from agio.core import api
from agio.core.api.utils import NOTSET
from .entity import DomainBase
from .package_release import APackageRelease

logger = logging.getLogger(__name__)


class APackage(DomainBase):
    domain_name = "package"

    @classmethod
    def get_data(cls, object_id: str) -> dict:
        return api.package.get_package(object_id)

    @classmethod
    def create(cls, name: str) -> 'APackage':
        package_id = api.package.create_package(name)
        return cls(package_id)

    def update(self,
               hidden: bool = NOTSET,
               disabled: bool = NOTSET,
               verified: bool = NOTSET,
               ) -> None:
        resp = api.package.update_package(
            self.id,
            hidden=hidden,
            disabled=disabled,
            verified=verified,
        )
        self._data.update(resp)

    @classmethod
    def iter(cls, limit: int = None) -> Generator['APackage', None, None]:
        for pkg in api.package.iter_packages():
            yield cls(pkg)

    def delete(self) -> None:
        return api.package.delete_package(self.id)

    @classmethod
    def find(cls, name: str) -> 'APackage' or None:
        pkg = api.package.find_package(name)
        if pkg is not None:
            return cls(pkg)

    @property
    def name(self):
        return self._data["name"]

    def get_release(self, version: str) -> APackageRelease:
        return APackageRelease.find(self.name, version=version)

    def iter_releases(self) -> Generator[APackageRelease, None, None]:
        for release_data in api.package.iter_package_releases(self.id):
            yield APackageRelease(release_data)

    def latest_release(self) -> APackageRelease:
        revision_id = api.package.get_latest_release(self.id)
        if revision_id is not None:
            return APackageRelease(revision_id)


