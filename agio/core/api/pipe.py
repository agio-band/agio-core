import os.path
from typing import Iterator
from uuid import UUID

from agio.core.api import client
from agio.core.api.utils import NOTSET
from agio.core.api.utils.query_tools import iter_query_list, deep_dict


# Product

def iter_products(
        entity_id: str|UUID,
        product_type_id: str = None,
        product_type_name: str = None,
        items_per_page: int = 50
    ) -> list:
    filters = deep_dict()
    filters['where']['entity']['id']['equalTo'] = entity_id
    if product_type_id:
        filters['where']['type']['id']['equalTo'] = product_type_id
    if product_type_name:
        filters['where']['type']['name']['equalTo'] = product_type_name
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
        variant: str,
        product_type_id: str = None,
        fields: dict|None = NOTSET,
    ):
    return client.make_query(
        'pipe/products/createProduct',
        input=dict(
            name=name,
            entity=entity_id,
            type=product_type_id,
            variant=variant,
            fields=fields,
        )
    )['data']['createPublish']['publishId']


def update_product(product_id: str,
                   name: str|None = None,
                   variant: str|None = None,
                   fields: dict|None = None):
    input_data = deep_dict()
    if name:
        input_data['name'] = name
    if variant:
        input_data['variant'] = variant
    if fields:
        input_data['fields'] = fields
    return client.make_query(
        'pipe/products/updatePublish',
        id=product_id,
        input=input_data,
    )['data']['updatePublish']['ok']


def find_product(entity_id: str|UUID, name: str, variant: str):
    filters = deep_dict()
    filters['where']['entity']['id']['equalTo'] = entity_id
    if name:
        filters['where']['name']['equalTo'] = name
    if variant:
        filters['where']['variant']['equalTo'] = variant
    resp = client.make_query(
        'pipe/products/getProductList',
        filter=filters,
        first=1
    )
    if resp['data']['publishes']['edges']:
        return resp['data']['publishes']['edges'][0]['node']

# product type

def iter_product_types(items_per_page: int = 50):
    yield from iter_query_list(
        'pipe/product_types/getProductTypeList',
        'publishTypes',
        items_per_page=items_per_page,
    )


def get_product_type(product_type_id: str):
    return client.make_query(
        'pipe/product_types/getProductTypeById',
        id=product_type_id,
    )['data']['publishType']


def get_product_type_by_name(name: str):
    resp = client.make_query(
        'pipe/product_types/getProductTypeByName',
        name=name,
    )
    if resp['data']['publishTypes']['edges']:
        return resp['data']['publishTypes']['edges'][0]['node']


def create_product_type(name, description, config: dict = None, data_type: str = None):
    return client.make_query(
        'pipe/product_types/createProductType',
        input=dict(
            name=name,
            description=description,
            config=config or {},
            dataType=data_type or "",
        )
    )['data']['createPublishType']['publishTypeId']


def update_product_type(
        publish_type_id: str,
        config: dict = None,
        data_type: str = None,
):
    input_data = deep_dict()
    if config:
        input_data['config'] = config
    if data_type:
        input_data['dataType'] = data_type
    return client.make_query(
        'pipe/product_types/updatePublishType',
        id=publish_type_id,
        input=input_data,
    )['data']['updatePublishType']['ok']


# Published Version

def iter_prodict_versions(
        product_id: str = None,
        items_per_page: int = 50
):
    filters = deep_dict()
    filters['where']['publish']['id']['equalTo'] = product_id
    yield from iter_query_list(
        'pipe/versions/getVersionList',
        'publishVersions',
        variables=dict(
          filter=filters
        ),
        items_per_page=items_per_page,
    )


# versions

def get_version(version_id: str|UUID):
    return client.make_query(
        'pipe/versions/getVersionById',
        id=version_id,
    )['data']['publishVersion']


def create_version(
        product_id: str|UUID,
        version: str,
        task_id: str|UUID,
        publish_session_id: str,
        fields: dict = None,
        dependencies: list[str] = None
        ):
    input_data = dict(
            name=version,
            publish=product_id,
            entity=task_id,
            publishSession=str(publish_session_id),
            fields=fields
        )
    if dependencies:
        input_data['upstreams'] = dependencies
    return client.make_query(
        'pipe/versions/createVersion',
        input=input_data
    )['data']['createPublishVersion']['publishVersionId']


def update_version(
        version_id: str|UUID,
        fields: dict,
        dependencies: list[str] = NOTSET):
    update_data = {}
    if fields:
        update_data['fields'] = fields
    if dependencies:
        update_data['upstreams'] = dependencies
    if not update_data:
        raise ValueError('Nothing to update')
    return client.make_query(
        'pipe/versions/updateVersion',
        id=version_id,
        input=update_data
    )


def delete_version(version_id: str|UUID) -> bool:
    return client.make_query(
        'pipe/versions/deleteVersion',
        id=version_id
    )['data']['deletePublishVersion']['ok']


def get_next_version_number(product_id: str|UUID) -> int:
    response =  client.make_query(
        'pipe/versions/getLatestVersion',
        publishId=product_id,
    )
    versions = response['data']['publishVersions']['edges']
    if versions:
        return int(versions[0]['node']['name'].lower().strip('v'))+1
    else:
        return 1



# publish file

def create_publish_file(
        version_id: str|UUID,
        path: str,
        name: str = None
    ) -> str:
    name = name or os.path.basename(path)
    return client.make_query(
        'pipe/published_file/createPublishFile',
        # input=dict(
        name=name,
        path=path,
        publishVersion=version_id,
        # )
    )["data"]["createPublishFile"]["publishFileId"]


def get_published_file(published_file_id: str|UUID):
    return client.make_query(
        'pipe/published_file/getPublishedFile',
        id=published_file_id,
    )["data"]["publishFile"]


def iter_publish_files(
        version_id: str|UUID,
        path: str = NOTSET,
        name: str = NOTSET,
        use_regex: bool = False,
        items_per_page: int = 50
    ):
    filters = deep_dict()
    filters['where']['publishVersion']['id']['equalTo'] = version_id
    if name:
        filters['where']['name']['regExp' if use_regex else 'equalTo'] = name
    if path:
        filters['where']['path']['regExp' if use_regex else 'equalTo'] = path
    yield from iter_query_list(
        'pipe/published_file/getPublishFileList',
        'publishFiles',
        variables=dict(
            filter=filters,
        ),
        items_per_page=items_per_page
    )


# Publish session

def get_publish_session(session_id: str|UUID):
    return client.make_query(
        'pipe/publish_session/getPublishSessionById',
        id=session_id,
    )["data"]["publishSession"]


# class PublishStatus:
#     ready
#     to
#     review
#     viewed
#     sup
#     okay
#     dir
#     okay
#     santa is coming
#     approved


def create_publish_session(
        entity_id: str|UUID,
        state: str = None,
        status: str = None,
        workspace_settings_id: str = None,
        comment: str = None,
        data: dict = None,
) -> str:
    input_data = dict(
        entity=str(entity_id),
        state=state or 'PENDING', # TODO add enum
        status=status or 'rvw', # TODO add enum
        workspaceSettingsId=workspace_settings_id,
        comment=comment or '',
        data=data or {}
    )
    return client.make_query(
        'pipe/publish_session/createPublishSession',
        input=input_data
    )['data']['createPublishSession']['publishSessionId']


def update_publish_session(
        session_id: str|UUID,
        state: str = NOTSET,
        status: str = NOTSET,
        comment: str = NOTSET,
        data: dict = NOTSET) -> dict:
    update_data = {}
    if state:
        update_data['state'] = state
    if status:
        update_data['status'] = status
    if comment:
        update_data['comment'] = comment
    if data:
        if not isinstance(data, dict):
            raise TypeError('data must be a dict')
        update_data['data'] = data
    if not update_data:
        raise ValueError('Nothing to update')
    return client.make_query(
        'pipe/publish_session/updatePublishSession',
        id=session_id,
        input=update_data
    )['data']['updatePublishSession']['ok']


def iter_publish_sessions(project_id: str|UUID, items_per_page: int = 25) -> Iterator[dict]:
    filters = deep_dict()
    filters['where']['entity']['project']['id']['equalTo'] = project_id
    yield from iter_query_list(
        'pipe/publish_session/getPublishSessionList',
        'publishSessions',
        variables=dict(
            filter=filters,
        ),
        items_per_page=items_per_page
    )