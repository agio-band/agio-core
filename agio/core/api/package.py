from uuid import UUID
from . import client


# packages

def get_package(package_id: str|UUID) -> dict:
    return client.make_query(
        'workspace/package/getPackage',
        id=package_id,
    )['data']['package']


def create_package(name: str) -> str:
    return client.make_query(
        'workspace/package/createPackage',
            name=name,
    )['data']['createPackage']['packageId']


def update_package(
        package_id: UUID|str,
        hidden: bool = None,
        disabled: bool = None,
        verified: bool = None
    ):
    return client.make_query(
        'workspace/package/updatePackage',
        id=package_id,
        hidden=hidden,
        disabled=disabled,
        verified=verified,
    )['data']['updatePackage']['ok']


def get_package_list(
        items_per_page: int = 10,
        after: str = None,
        tags: list[str] = None,
    ) -> dict:
    data = client.make_query(
        'workspace/package/getPackageList',
        first=items_per_page,
        afterCursor=after,
    )
    return dict(
        data=[x['node'] for x in data['data']['packages']['edges']],
        pageInfo=data['data']['packages']['pageInfo'],
    )


# releases

def create_package_release(
        package_id: UUID|str,
        version: str,
        label: str,
        description: str,
        assets: dict,
        meta_data: dict = None
    ) -> dict:
    return client.make_query(
        'workspace/release/createPackageRelease',
        packageId=package_id,
        name=version,
        label=label,
        description=description,
        assets=assets,
        metaData=meta_data,
    )["createPackageRelease"]["packageReleaseId"]


def get_package_release(release_id: UUID) -> dict:
    return client.make_query(
        'workspace/release/getPackageRelease',
        id=release_id,
    )['data']['packageRelease']


def get_package_release_list(
        package_id: UUID|str,
        search: str = None,
        items_per_page: int = 10,
        after: str = None
    ) -> list:
    return client.make_query(
        'workspace/release/getPackageReleaseList',
        first=items_per_page,
        afterCursor=after,
        packageId=package_id,
    )['data']['packageReleases']['packageReleaseList']


def update_package_release(
        release_id: UUID|str,
        version: str,
        label: str,
        description: str,
        assets: dict,
        meta_data: dict = None
    ) -> dict:
    return client.make_query(
        'workspace/release/updatePackageRelease',
        id=release_id,
        name=version,
        label=label,
        description=description,
        assets=assets,
        metadata=meta_data,
    )['data']['updatePackageRelease']['ok']


def delete_package_release(release_id: UUID) -> bool:
    return client.make_query(
        'workspace/release/deletePackageRelease',
        id=release_id,
    )['data']['deletePackageRelease']['ok']
