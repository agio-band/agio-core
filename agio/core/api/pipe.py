import os.path
from typing import Iterator, Generator
from uuid import UUID

from agio.core.api import client as default_client
from agio.core.api.utils import NOTSET, api_call
from agio.core.api.utils.query_tools import iter_query_list
from agio.tools.data_helpers import deep_tree


# Product

@api_call
def iter_products(
        entity_id: str|UUID = None,
        project_id: str|UUID = None,
        product_type_id: str = None,
        product_type_name: str = None,
        items_per_page: int = 50, 
        client=default_client
    ) -> Generator[dict, None, None]:
    if not any([entity_id, project_id]):
        raise ValueError('Project ID or Entity ID not provided')
    filters = deep_tree()
    if entity_id:
        filters['where']['entity']['id']['equalTo'] = entity_id
    if project_id:
        filters['where']['entity']['project']['id']['equalTo'] = project_id
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
        },
        client=client
    )


@api_call
def get_product(product_id: UUID, client=default_client):
    return client.make_query(
        'pipe/products/getProductById',
        id=product_id,
    )['data']['publish']


@api_call
def create_product(
        name: str,
        entity_id: str|UUID,
        variant: str,
        product_type_id: str = None,
        fields: dict|None = NOTSET,
        client=default_client
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


@api_call
def update_product(product_id: str,
                   name: str|None = None,
                   variant: str|None = None,
                   fields: dict|None = None,
                   client=default_client):
    input_data = deep_tree()
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


@api_call
def find_product(entity_id: str|UUID, name: str, variant: str, client=default_client) -> dict|None:
    filters = deep_tree()
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

@api_call
def iter_product_types(items_per_page: int = 50, filter_field: str|None = 'is_agio_type', client=default_client):
    for product_data in iter_query_list(
        'pipe/product_types/getProductTypeList',
        'publishTypes',
        items_per_page=items_per_page,
        client=client
        ):
        # filter for agio product types
        if filter_field:
            if product_data.get('config', {}).get(filter_field):
                yield product_data
        else:
            yield product_data


@api_call
def get_product_type(product_type_id: str, client=default_client) -> dict:
    return client.make_query(
        'pipe/product_types/getProductTypeById',
        id=product_type_id,
    )['data']['publishType']


@api_call
def get_product_type_by_name(name: str, client=default_client) -> dict|None:
    resp = client.make_query(
        'pipe/product_types/getProductTypeByName',
        name=name,
    )
    if resp['data']['publishTypes']['edges']:
        return resp['data']['publishTypes']['edges'][0]['node']


@api_call
def create_product_type(name, description, config: dict = None, data_type: str = None, client=default_client) -> dict:
    return client.make_query(
        'pipe/product_types/createProductType',
        input=dict(
            name=name,
            description=description,
            config=config or {},
            dataType=data_type or "",
        )
    )['data']['createPublishType']['publishTypeId']


@api_call
def update_product_type(
        publish_type_id: str,
        config: dict = None,
        data_type: str = None,
        client=default_client
):
    input_data = deep_tree()
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

@api_call
def iter_prodict_versions(
        product_id: str = None,
        entity_id: str = None,
        project_id: str = None,
        items_per_page: int = 50,
        client=default_client
):
    filters = deep_tree()
    if product_id:
        filters['where']['publish']['id']['equalTo'] = product_id
    if entity_id:
        filters['where']['entity']['id']['equalTo'] = entity_id
    if project_id:
        filters['where']['entity']['project']['id']['equalTo'] = project_id
    yield from iter_query_list(
        'pipe/versions/getVersionList',
        'publishVersions',
        variables=dict(
          filter=filters
        ),
        items_per_page=items_per_page,
        client=client
    )


# versions
@api_call
def get_version(version_id: str|UUID, client=default_client):
    return client.make_query(
        'pipe/versions/getVersionById',
        id=version_id,
    )['data']['publishVersion']


@api_call
def create_version(
        product_id: str|UUID,
        version: str,
        task_id: str|UUID,
        publish_session_id: str,
        fields: dict = None,
        dependencies: list[str] = None,
        client=default_client
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


@api_call
def update_version(
        version_id: str|UUID,
        fields: dict = NOTSET,
        dependencies: list[str] = NOTSET,
        publish_session_id: str|UUID = NOTSET,
        client=default_client):
    update_data = {}
    if fields:
        update_data['fields'] = fields
    if dependencies:
        update_data['upstreams'] = dependencies
    if publish_session_id:
        update_data['publishSessionId'] = publish_session_id
    if not update_data:
        raise ValueError('Nothing to update')
    return client.make_query(
        'pipe/versions/updateVersion',
        id=version_id,
        input=update_data
    )


@api_call
def delete_version(version_id: str|UUID, client=default_client) -> bool:
    return client.make_query(
        'pipe/versions/deleteVersion',
        id=version_id
    )['data']['deletePublishVersion']['ok']


@api_call
def get_next_version_number(product_id: str|UUID, client=default_client) -> int:
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
@api_call
def create_publish_file(
        version_id: str|UUID,
        path: str,
        name: str = None,
        client=default_client
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


@api_call
def get_published_file(published_file_id: str|UUID, client=default_client):
    return client.make_query(
        'pipe/published_file/getPublishedFile',
        id=published_file_id,
    )["data"]["publishFile"]


@api_call
def iter_publish_files(
        version_id: str|UUID,
        path: str = NOTSET,
        name: str = NOTSET,
        use_regex: bool = False,
        items_per_page: int = 50,
        client=default_client
    ):
    filters = deep_tree()
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
        items_per_page=items_per_page,
        client=default_client
    )


# Publish session
@api_call
def get_publish_session(session_id: str|UUID, client=default_client):
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

@api_call
def create_publish_session(
        entity_id: str|UUID,
        name: str,
        version: int,
        state: str = None,
        status: str = None,
        workspace_settings_id: str = None,
        comment: str = None,
        data: dict = None,
        client=default_client
) -> str:
    input_data = dict(
        entity=str(entity_id),
        name=name,
        number=version,
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


@api_call
def update_publish_session(
        session_id: str|UUID,
        name: str = NOTSET,
        state: str = NOTSET,
        status: str = NOTSET,
        comment: str = NOTSET,
        data: dict = NOTSET,
        client=default_client) -> dict:
    update_data = {
        'name': name,
        'state': state,
        'status': status,
        'comment': comment,
        'data': data
    }
    if data:
        if not isinstance(data, dict):
            raise TypeError('data must be a dict')
    return client.make_query(
        'pipe/publish_session/updatePublishSession',
        id=session_id,
        input=update_data
    )['data']['updatePublishSession']['ok']


@api_call
def iter_publish_sessions(project_id: str|UUID, items_per_page: int = 25, client=default_client) -> Iterator[dict]:
    filters = deep_tree()
    filters['where']['entity']['project']['id']['equalTo'] = project_id
    yield from iter_query_list(
        'pipe/publish_session/getPublishSessionList',
        'publishSessions',
        variables=dict(
            filter=filters,
        ),
        items_per_page=items_per_page,
        client=client
    )


@api_call
def delete_publish_session(session_id: str|UUID, client=default_client):
    return client.make_query(
        'pipe/publish_session/deletePublishSession',
        id=session_id,
    )['data']['deletePublishSession']['ok']


@api_call
def get_next_session_version(entity_id: str|UUID, client=default_client):
    result = client.make_query(
        'pipe/publish_session/getLatestPublishSessionForEntity',
        entityId=entity_id,
        )
    items = result["data"]["publishSessions"]["edges"]
    if items:
        return items[0]["node"]["number"] + 1
    return 1