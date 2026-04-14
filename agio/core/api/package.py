from typing import Iterator
from uuid import UUID
from . import client as default_client
from .utils import NOTSET
from .utils.query_tools import iter_query_list
from agio.core.api._utils import set_client

# packages

@set_client
def get_package(package_id: str|UUID, client=default_client) -> dict:
    return client.make_query(
        'ws/package/getPackage',
        id=package_id,
    )['data']['package']


@set_client
def create_package(name: str, client=default_client) -> str:
    return client.make_query(
        'ws/package/createPackage',
            name=name,
    )['data']['createPackage']['packageId']


@set_client
def find_package(name: str, client=default_client) -> dict|None:
    resp = client.make_query(
        'ws/package/findPackage',
        name=name,
    )['data']['packages']['edges']
    if resp:
        return resp[0]['node']


@set_client
def update_package(
        package_id: UUID|str,
        hidden: bool = NOTSET,
        disabled: bool = NOTSET,
        verified: bool = NOTSET,
        client=default_client
    ):
    return client.make_query(
        'ws/package/updatePackage',
        id=package_id,
        hidden=hidden,
        disabled=disabled,
        verified=verified,
    )['data']['updatePackage']['ok']


# def get_package_list(
#         items_per_page: int = 10,
#         after: str = None,
#         tags: list[str] = None,
#     ) -> dict:
#     data = client.make_query(
#         'workspace/package/getPackageList',
#         first=items_per_page,
#         afterCursor=after,
#     )
#     return dict(
#         data=[x['node'] for x in data['data']['packages']['edges']],
#         pageInfo=data['data']['packages']['pageInfo'],
#     )


@set_client
def iter_packages(limit: int = None, client=default_client) -> Iterator[dict]:
    yield from iter_query_list(
        'ws/package/getPackageList',
        entities_data_key='packages',
        limit=limit,
        client=client
    )


@set_client
def delete_package(package_id: str, client=default_client) -> None:
    return client.make_query(
        'ws/package/deletePackage',
        id=package_id,
    )

# releases

@set_client
def create_package_release(
        package_id: UUID|str,
        version: str,
        assets: dict,
        label: str,
        description: str = NOTSET,
        metadata: dict = NOTSET,
        client=default_client
    ) -> str:
    return client.make_query(
        'ws/release/createPackageRelease',
        packageId=package_id,
        name=version,
        label=label,
        assets=assets,
        description=description or '',
        metadata=metadata,
    )["data"]["createPackageRelease"]["packageReleaseId"]


@set_client
def get_package_release(release_id: UUID|str, client=default_client) -> dict:
    return client.make_query(
        'ws/release/getPackageRelease',
        id=release_id,
    )['data']['packageRelease']


# def get_package_releases_for_package_id(package_id: UUID|str, client=default_client) -> dict:
#     return client.make_query(
#         'ws/release/getPackageReleasesForPackageId',
#     )


@set_client
def get_package_release_by_name_and_version(package_name: str, version: str, client=default_client) -> dict|None:
    resp = client.make_query(
        'ws/release/findPackageRelease',
        package_name=package_name,
        version=version,
    )
    if resp['data']['packageReleases']['edges']:
        return resp['data']['packageReleases']['edges'][0]['node']

# def get_package_release_list(
#         package_id: UUID|str,
#         search: str = None,
#         items_per_page: int = 10,
#         after: str = None
#     ) -> list:
#     return client.make_query(
#         'workspace/release/getPackageReleaseList',
#         first=items_per_page,
#         afterCursor=after,
#         packageId=package_id,
#     )['data']['packageReleases']['edges']


@set_client
def iter_package_releases(package_id: UUID|str, limit: int = None, client=default_client) -> Iterator[dict]:
    yield from iter_query_list(
        'ws/release/getPackageReleaseList',
        entities_data_key='packageReleases',
        variables={'packageId': package_id},
        limit=limit,
        client=default_client
    )


@set_client
def update_package_release(
        release_id: UUID|str,
        label: str,
        description: str,
        assets: dict,
        metadata: dict = None,
        client=default_client
    ) -> dict:
    return client.make_query(
        'ws/release/updatePackageRelease',
        id=release_id,
        label=label,
        description=description,
        assets=assets,
        metadata=metadata,
    )['data']['updatePackageRelease']['ok']


@set_client
def delete_package_release(release_id: UUID, client=default_client) -> bool:
    return client.make_query(
        'ws/release/deletePackageRelease',
        id=release_id,
    )['data']['deletePackageRelease']['ok']


@set_client
def get_latest_release(package_id: str, client=default_client) -> dict|None:
    resp = client.make_query(
        'ws/release/getLatestRelease',
        packageId=package_id,
    )["data"]["packageReleases"]["edges"]
    if resp:
        return resp[0]['node']
