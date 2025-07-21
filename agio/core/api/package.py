from typing import Iterator
from uuid import UUID
from . import client
from .utils import NOTSET
from .utils.query_tools import iter_entities


# packages

def get_package(package_id: str|UUID) -> dict:
    return client.make_query(
        'ws/package/getPackage',
        id=package_id,
    )['data']['package']


def create_package(name: str) -> str:
    return client.make_query(
        'ws/package/createPackage',
            name=name,
    )['data']['createPackage']['packageId']


def find_package(name: str) -> dict:
    resp = client.make_query(
        'ws/package/findPackage',
        name=name,
    )['data']['packages']['edges']
    if resp:
        return resp[0]['node']


def update_package(
        package_id: UUID|str,
        hidden: bool = NOTSET,
        disabled: bool = NOTSET,
        verified: bool = NOTSET
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


def iter_packages(limit: int = None) -> Iterator[dict]:
    yield from iter_entities(
        'ws/package/getPackageList',
        entities_data_key='packages',
        limit=limit,
    )


def delete_package(package_id: str) -> None:
    return client.make_query(
        'ws/package/deletePackage',
        id=package_id,
    )

# releases

def create_package_release(
        package_id: UUID|str,
        version: str,
        assets: dict,
        label: str,
        description: str = NOTSET,
        metadata: dict = NOTSET
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


def get_package_release(release_id: UUID|str) -> dict:
    return client.make_query(
        'ws/release/getPackageRelease',
        id=release_id,
    )['data']['packageRelease']


def get_package_releases_for_package_id(package_id: UUID|str) -> dict:
    return client.make_query(
        'ws/release/getPackageReleasesForPackageId',
    )


def get_package_release_by_name_and_version(package_name: str, version: str) -> dict:
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


def iter_package_releases(package_id: UUID|str, limit: int = None) -> Iterator[dict]:
    yield from iter_entities(
        'ws/release/getPackageReleaseList',
        entities_data_key='packageReleases',
        variables={'packageId': package_id},
        limit=limit,
    )


def update_package_release(
        release_id: UUID|str,
        label: str,
        description: str,
        assets: dict,
        metadata: dict = None
    ) -> dict:
    return client.make_query(
        'ws/release/updatePackageRelease',
        id=release_id,
        label=label,
        description=description,
        assets=assets,
        metadata=metadata,
    )['data']['updatePackageRelease']['ok']


def delete_package_release(release_id: UUID) -> bool:
    return client.make_query(
        'ws/release/deletePackageRelease',
        id=release_id,
    )['data']['deletePackageRelease']['ok']


def get_latest_release(package_id: str) -> dict:
    resp = client.make_query(
        'ws/release/getLatestRelease',
        packageId=package_id,
    )["data"]["packageReleases"]["edges"]
    if resp:
        return resp[0]['node']
