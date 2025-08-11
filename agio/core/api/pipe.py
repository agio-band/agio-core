from uuid import UUID

from agio.core.api import client
from agio.core.api.utils import NOTSET
from agio.core.api.utils.query_tools import iter_query_list, deep_dict


# Product

def iter_products(
        entity_id: str|UUID,
        product_type: str = None,
        items_per_page: int = 50
    ) -> list:
    filters = deep_dict()
    filters['where']['entity']['id']['equalTo'] = entity_id
    if product_type:
        filters['type'] = product_type
    yield from iter_query_list(
        'pipe/products/getProductList',
        'publishes',
        items_per_page=items_per_page,
        variables={
            'filter':filters
        }
    )


def get_product(product_id: UUID):
    return client.make_query(
        'pipe/products/getProductById',
        id=product_id,
    )['data']['publish']


def create_product(
        name: str,
        entity_id: str|UUID,
        product_type: str,
        variant: str,
        fields: dict|None = NOTSET,
    ):
    return client.make_query(
        'pipe/products/createProduct',
        name=name,
        entityId=entity_id,
        type=product_type,
        variant=variant,
        fields=fields,
    )['data']['createPublish']['publishId']


def find_product(entity_id: str|UUID, product_type: str, variant: str):
    filters = deep_dict()
    filters['where']['entity']['id']['equalTo'] = entity_id
    if product_type:
        filters['where']['type']['equalTo'] = product_type
    if variant:
        filters['where']['variant']['equalTo'] = variant
    resp = client.make_query(
        'pipe/products/getProductList',
        filter=filters,
        limit=1
    )
    if resp['data']['publishes']['edges']:
        return resp['data']['publishes']['edges'][0]['node']


# Published Version

def iter_prodict_versions(
        entity_id: UUID,
        product_type: str = None,
        variant: UUID = None,
        items_per_page: int = 50
):
    filters = deep_dict()
    filters['where']['entity']['id']['equalTo'] = entity_id
    if variant:
        filters['where']['variant']['equalTo'] = variant
    if product_type:
        filters['where']['type']['equalTo'] = product_type
    yield from iter_query_list(
        'pipe/versions/getVersionList',
        'publishVersions',
        variables=dict(
          filter=filters
        ),
        items_per_page=items_per_page,
    )


def get_product_version(version_id: UUID):
    return client.make_query(
        'pipe/versions/getVersionById',
        id=version_id,
    )


def create_product_version(
        version: str,
        product_id: UUID,
        task_id: UUID,
        fields: dict,
):
    return client.make_query(
        'pipe/versions/createVersion',
        name=version,
        publish=product_id,
        entity=task_id,
        fields=fields
    )

# versions

def get_version(version_id: str|UUID):
    return client.make_query(
        'pipe/versions/getVersionById',
        id=version_id,
    )['data']['publishVersion']


def update_version(version_id: str|UUID, fields: dict):
    return client.make_query(
        'pipe/versions/updateVersion',
        id=version_id,
        fields=fields
    )


def get_next_version_number(
        task_id: str|UUID,
        product_id: str|UUID,
) -> int:
    filters = deep_dict()
    filters['where']['entity']['id']['equalTo'] = task_id
    filters['where']['publish']['id']['equalTo'] = product_id
    response =  client.make_query(
        'pipe/versions/getLatestVersion',
        filter=filters
    )
    versions = response['data']['publishVersions']['edges']
    if versions:
        return int(versions[0]['node']['name'])+1
    else:
        return 1


def create_version(
        version: str,
        product_id: UUID,
        task_id: UUID,
        fields: dict,
        ):
    return client.make_query(
        'pipe/versions/createVersion',
        name=version,
        publish=product_id,
        entity=task_id,
        fields=fields
    )['data']['createPublishVersion']['publishVersionId']
