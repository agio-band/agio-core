import os
from typing import Self, Iterator

from agio.core import api, env_names
from agio.core.api.utils import NOTSET
from . import APackageRelease, APackage
from .entity import DomainBase
from .workspace_revision import AWorkspaceRevision
from ..exceptions import RequestError


class AWorkspace(DomainBase):
    domain_name = 'workspace'

    @classmethod
    def get_data(cls, object_id: str) -> Self:
        return api.workspace.get_workspace(object_id)

    def update(self, name: str = NOTSET, description: str = None) -> None:
        if api.workspace.update_workspace(
            self.id,
            name=name,
            description=description,
        ):
            self.reload()

    @classmethod
    def iter(cls, company_id: str = None) -> Iterator[Self]:
        company_id = company_id or api.desk.get_current_company()['id']
        for data in api.workspace.iter_workspaces(company_id=company_id):
            yield cls(data)

    @classmethod
    def create(cls, company_id: str, name: str, description: str = NOTSET) -> Self:
        ws_id = api.workspace.create_workspace(
            company_id=company_id,
            name=name,
            description=description,
        )
        return cls(ws_id)

    def delete(self) -> bool:
        return api.workspace.delete_workspace(self.id)

    @classmethod
    def find(cls, company_id: str = None, name: str = NOTSET) -> Self:
        company_id = company_id or api.desk.get_current_company()['id']
        data = api.workspace.find_workspace(company_id=company_id, name=name)
        if data:
            return cls(data)

    @classmethod
    def current(cls):
        ws_id = os.getenv(env_names.WORKSPACE_ENV_NAME)
        if not ws_id:
            raise RuntimeError('Workspace is not initialized')
        return cls(ws_id)

    def get_current_revision(self):
        revision = api.workspace.get_revision_by_workspace_id(self.id)
        if revision:
            return AWorkspaceRevision(revision)

    def get_manager(self):
        from agio.core.pkg import AWorkspaceManager

        return AWorkspaceManager(self.get_current_revision())

    def _find_release(self, input_data: dict|str|APackageRelease|APackage) -> APackageRelease:
        if isinstance(input_data, APackageRelease):
            return input_data
        elif isinstance(input_data, APackage):
            latest_release = input_data.latest_release()
            if not latest_release:
                raise Exception(f'Release for package {input_data} not found')
            return latest_release
        elif isinstance(input_data, str):

            try:
                release = api.package.get_package_release(input_data)
                return APackageRelease(release)
            except RequestError:
                try:
                    pkg = APackage.find(name=input_data)
                    return pkg.latest_release()
                except RequestError:
                    raise Exception(f'Package or release {input_data} not found')
        elif isinstance(input_data, dict):
            release = api.package.get_package_release_by_name_and_version(
                package_name=input_data['name'],
                version=input_data['version'],
            )
            if not release:
                raise Exception(f'Package release {input_data} not found')
            return APackageRelease(release)
        else:
            raise Exception(f'Unknown input type {type(input_data)}')

    def set_package_list(
            self,
            packages: list[dict|str],
            set_current: bool = False,
            comment: str = None,
            layout: dict = None,
    ):
        if not packages:
            raise Exception(f'No packages to set')
        # collect releases
        releases: list[APackageRelease] = [self._find_release(p) for p in packages]
        if not releases:
            raise Exception(f'No package releases found')
        pkg_names = [p.get_package_name() for p in releases]
        for pkg_name in pkg_names:
            if pkg_names.count(pkg_name)>1:
                raise Exception(f'Multiple packages with same name: {pkg_name}')
        names = [rel.get_package_name() for rel in releases]
        # check core package exists
        if 'agio_core' not in names:
            raise Exception(f'agio-core package is required but not added')
        release_ids = [rel.id for rel in releases]
        # create revision
        result = api.workspace.create_revision(
            workspace_id=self.id,
            package_release_ids=release_ids,
            set_current=set_current,
            status='ready', # TODO change to "sync"
            comment=comment,
            layout=layout or NOTSET,
        )
        return AWorkspaceRevision(result)

