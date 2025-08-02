from uuid import UUID

from agio.core.api.utils.query_tools import iter_query_list
from agio.core.api import client
from agio.core.exceptions import ProjectNotExists, EntityNotExists


# project

def get_project(project_id: str|UUID) -> dict:
    return client.make_query(
        'track/projects/getProjectById',
        id=project_id,
    )['data']['project']


def get_project_by_name(company_id: str|UUID, name: str) -> dict:
    data = client.make_query(
        'track/projects/findProject',
        company_id=str(company_id),
        name=name,
    )
    if data['data']['projects']['edges']:
        return data['data']['projects']['edges'][0]
    raise ProjectNotExists


def create_project(payload: dict) -> dict:
    pass


def update_project(project_id: UUID, payload: dict) -> dict:
    pass


def delete_project(project_id: str|UUID) -> None:
    pass


# entities

def get_entity(entity_id: str|UUID) -> dict:
    data = client.make_query(
        'track/entities/getEntityById',
        id=str(entity_id),
    )
    if data['data']['entities']['edges']:
        return data['data']['entities']['edges'][0]
    raise EntityNotExists


def get_entity_by_name(project_id: str|UUID, entity_class: str, name: str) -> dict:
    data = client.make_query(
        'track/entities/getEntityByName',
        projectId=str(project_id),
        className=entity_class,
        name=name,
    )
    if data['data']['entities']['edges']:
        return data['data']['entities']['edges'][0]
    raise EntityNotExists


def iter_entities(
        project_id: str|UUID,
        entity_class: str,
        parent_id: str|UUID = None,
        name: str = None,       # supported regex
        items_per_page: int = 50
) -> list:
    where_filter = {
        'project': {'id': {'equalTo': project_id}},
        'class': {'name': {'equalTo', entity_class}}
    }
    if parent_id:
        where_filter['parent'] = {'id': {'equalTo': parent_id}}
    if name:
        where_filter['name'] = {'regExp': name}
    yield from iter_query_list(
        'track/entities/getEntityList',
        'entities',
        variables={
            'where':where_filter,
        },
        items_per_page=items_per_page,
    )


def get_entity_children(entity_id: str|UUID) -> list:
    yield from iter_query_list(
        'track/entities/findEntities',
        'entities',
        variables={
            'filter': {
                'where': {
                    'parentId': {'equalTo': entity_id},
                }
            },
            'order': {
                "sort": "NAME",
                "direction": "DESC" # ASC
            }
        }
    )


def get_entity_parent(entity: str|UUID|dict) -> list:
    parents = []
    if isinstance(entity, UUID|str):
        next_entity = get_entity(entity)
    else:
        next_entity = entity
    while next_entity['parentId']:
        parents.append(next_entity)
        next_entity = get_entity(next_entity['parentId'])
    return parents[1:]

