from __future__ import annotations

import logging
from typing import Generator

from agio.core import api
from agio.core.api.utils import NOTSET
from .base_object import BaseObject
from .package_release import APackageRelease

logger = logging.getLogger(__name__)


class APackage(BaseObject):
    object_name = "package"

    @classmethod
    def get_data(cls, object_id: str, client=None) -> dict:
        return api.package.get_package(object_id, client=client)

    @classmethod
    def create(cls, name: str, client=None) -> APackage:
        package_id = api.package.create_package(name, client=client)
        return cls(package_id, client=client)

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
            client=self.client,
        )
        self._data.update(resp)

    @classmethod
    def iter(cls, limit: int = None, client=None) -> Generator[APackage, None, None]:
        for pkg in api.package.iter_packages(client=client):
            yield cls(pkg, client=client)

    def delete(self) -> None:
        return api.package.delete_package(self.id, client=self.client)

    @classmethod
    def find(cls, name: str, client=None) -> APackage | None:
        pkg = api.package.find_package(name, client=client)
        if pkg is not None:
            return cls(pkg, client=client)
        return None

    @property
    def name(self):
        return self._data["name"]

    def get_release(self, version: str) -> APackageRelease:
        return APackageRelease.find(self.name, version=version)

    def iter_releases(self) -> Generator[APackageRelease, None, None]:
        for release_data in api.package.iter_package_releases(self.id, client=self.client):
            yield APackageRelease(release_data, client=self.client)

    def latest_release(self) -> APackageRelease|None:
        revision_id = api.package.get_latest_release(self.id, client=self.client)
        if revision_id is not None:
            return APackageRelease(revision_id, client=self.client)
        return None


