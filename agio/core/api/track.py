from functools import cache
from typing import Any, Iterator
from uuid import UUID

from agio.core.api.utils import NOTSET
from agio.core.api.utils.query_tools import iter_query_list, deep_dict
from agio.core.api import client
from agio.core.exceptions import ProjectNotExists, EntityNotExists


# project

def get_project(project_id: str|UUID) -> dict:
    return client.make_query(
        'track/projects/getProjectById',
        id=project_id,
    )['data']['project']


def get_project_by_name(company_id: str|UUID, name: str) -> dict:
    filters = dict(
        where=dict(
            name={'equalTo': name},
            company={'id': {'equalTo': company_id}},
        )
    )
    data = client.make_query(
        'track/projects/findProject',
        filter=filters,
    )
    if data['data']['projects']['edges']:
        return data['data']['projects']['edges'][0]['node']
    raise ProjectNotExists


def update_project(
        project_id: str|UUID,
        state: str = NOTSET,
        facility_ids: list[str] = NOTSET,
        fields: dict[str, Any] = NOTSET,
        workspace_id: str|UUID|None = NOTSET,
        revision_id: str|None = NOTSET,
) -> bool:
    input_data = dict(
        state=state,
        facilityIds=facility_ids,
        fields=fields,
        workspaceId=workspace_id,
        workspaceRevisionId=revision_id,
    )
    input_data = {k: v for k, v in input_data.items() if v is not NOTSET}
    if not input_data:
        raise ValueError('No input data provided')
    return client.make_query(
        'track/projects/updateProject',
        id=str(project_id),
        input=input_data
    )['data']['updateProject']['ok']


def iter_projects(company_id: str|UUID, has_workspace: bool = NOTSET, items_per_page: int = 50) -> Iterator[dict]:
    filters = deep_dict()
    filters['where']['company']['id']['equalTo'] = str(company_id)
    if has_workspace:
        filters['where']['workspaceId']['notNull'] = True
    return iter_query_list(
        'track/projects/projectsList',
        'projects',
        variables={
            "filter": filters,
        },
        limit=items_per_page
    )

def find_project(
        company_id: str|UUID = NOTSET,
        company_name: str|None = NOTSET,
        name: str = NOTSET,
        code: str = NOTSET,
        state: str = NOTSET,
) -> dict:
    filters = deep_dict()
    if company_id:
        filters['where']['company']['id']['equalTo'] = company_id
    if company_name:
        filters['where']['company']['name']['equalTo'] = company_name
    if name:
        filters['where']['name']['equalTo'] = name
    if code:
        filters['where']['code']['equalTo'] = code
    if state:
        filters['where']['state']['equalTo'] = state
    data = client.make_query(
        'track/projects/findProject',
        filter=filters
    )
    if data['data']['projects']['edges']:
        return data['data']['projects']['edges'][0]['node']


# entities

def get_entity(entity_id: str|UUID) -> dict:
    data = client.make_query(
        'track/entities/getEntityById',
        id=str(entity_id),
    )
    if data['data']['entities']['edges']:
        return data['data']['entities']['edges'][0]['node']
    raise EntityNotExists(detail='Entity not found: {}'.format(entity_id))


def get_entity_hierarchy(entity_id: str|UUID, depth: int = 10, include_source: bool = False) -> tuple[dict]:
    query_text = client.load_query('track/entities/getEntityHierarchy.graphql')
    part = client.load_query('track/entities/getEntityHierarchyPart.graphql')
    replace_pattern = '#{{PARENT-QUERY}}#'

    def format_query(text, depth):
        if depth > 0:
            plevel = '\n'.join([('  ' * depth) + x for x in part.split('\n')])
            text = text.replace(replace_pattern, format_query(plevel, depth=depth - 1))
        else:
            text = text.replace(replace_pattern, '')
        return text

    query = format_query(query_text, depth)
    data = client.make_query_raw(
        query,
        id=entity_id,
    )

    def iter_parents(entity: dict):
        parent = entity.pop('parent', None)
        yield entity
        if parent is not None:
            yield from iter_parents(parent)

    if data['data']['entities']['edges']:
        item = data['data']['entities']['edges'][0]['node']
        parents = tuple(iter_parents(item))
        if not include_source:
            parents = parents[1:]
        return tuple(reversed(parents))
    return tuple()



def get_entity_by_name(project_id: str|UUID, entity_class: str, name: str) -> dict:
    data = client.make_query(
        'track/entities/getEntityByName',
        projectId=str(project_id),
        className=entity_class,
        name=name,
    )
    if data['data']['entities']['edges']:
        return data['data']['entities']['edges'][0]['node']
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
        'class': {'name': {'equalTo': entity_class}}
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



def create_entity(project_id: str|UUID,
                  entity_class: str,
                  name: str,
                  parent_id: str = NOTSET,
                  fields: dict = NOTSET,
                  ) -> dict:
    class_id = get_entity_class_id(project_id, entity_class)
    return client.make_query(
        'track/entities/createEntity',
        input=dict(
            classId=class_id,
            name=name,
            projectId=project_id,
            parentId=parent_id,
            fields=fields or {},
            links=[],   # TODO
            classLinks=[], # TODO
            assignees=[] # TODO
        )
    )["data"]["createEntity"]["entityId"]


def update_entity(
        entity_id: str|UUID,
        name: str = NOTSET,
        fields: dict[str, Any] = NOTSET,
        # state: str = NOTSET,
    ):
    return client.make_query(
        'track/entities/updateEntity',
        id=str(entity_id),
        input={
            # 'state': state,
            'name': name,
            'fields': fields,
        },
    )


def delete_entity(entity_id: str|UUID) -> None:
    raise NotImplementedError


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

# entity classes

@cache
def get_entity_class_id(project_id: str | UUID,
                        entity_class: str) -> UUID:
    resp = client.make_query(
        'track/entity_classes/getEntityClassByName',
        projectId=str(project_id),
        name=entity_class,
    )['data']['entityClasses']['edges']
    if resp:
        return resp[0]['node']['id']
    raise EntityNotExists