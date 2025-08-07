import logging
import os
from pathlib import Path
from typing import Self, Iterator

from agio.core import api
from agio.core.api.utils import NOTSET
from agio.core.exceptions import PackageError
from agio.core.utils import app_dirs
from agio.core.utils.network import download_file
from agio.core.utils.repository_utils import filter_compatible_package
from .entity import DomainBase

logger = logging.getLogger(__name__)


class APackageRelease(DomainBase):
    type_name = 'package_release'

    def __repr__(self):
        return f'<{self.__class__.__name__} {self.get_package_name()} v{self.get_version()} ({self.id!r})>'

    @classmethod
    def get_data(cls, object_id: str) -> dict:
        return api.package.get_package_release(object_id)

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
        return self._data['package']['id']

    def get_package_name(self) -> str:
        return self._data['package']['name']

    def get_package(self) -> "APackage":
        from .package import APackage
        return APackage(self.get_package_id())

    def get_assets(self):
        return self._data.get('assets', {}).get('whl')

    def get_version(self):
        return self._data.get('name')

    def get_installation_command(self, **kwargs):
        package = self.get_package()
        force_download = kwargs.pop('force_download', False)

        if assets := self.get_assets():
            name_list = [asset['name'] for asset in assets]
            name = filter_compatible_package(name_list)
            if not name:
                raise PackageError(f"Error fetching whl file, Compatible asset not found")
            url = next(iter([x['url'] for x in assets if x['name'] == name]))
            if url.startswith('https'):
                cmd = url
                # # TODO: check if is private package saved on private store
                # logger.debug(f'Download file {name}: {url}')
                # cmd = download_file(
                #     url,
                #     Path(app_dirs.temp_dir(), 'releases').as_posix(),
                #     name,
                #     skip_exists=not force_download
                # )
            elif url.startswith('git+'):
                cmd = url
            else:
                path = os.path.expandvars(Path(url).expanduser())
                if not os.path.exists(path):
                    raise PackageError(f"Error fetching package {self}, file not found: {url}")
                cmd = path
            return cmd
        elif package.source_url:
            # use source repository path. Repository must be installable! (pyproject.toml)
            cmd = os.path.expandvars(Path(package.source_url).expanduser())
        else:
            raise PackageError(f"Error fetching package {self}, installation command not created")
        return cmd
