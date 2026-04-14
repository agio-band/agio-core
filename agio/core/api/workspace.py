from typing import Iterator
from uuid import UUID

from . import client as default_client
from .utils import NOTSET
from .utils.query_tools import iter_query_list
from ..exceptions import RevisionNotExists, SettingsRevisionNotExists, WorkspaceNotExists, ProjectNotExists, \
    ProjectWorkspaceNotSet
from . import track
from agio.tools.data_helpers import deep_tree
from agio.core.api._utils import set_client


@set_client
def get_workspace(workspace_id: UUID|str, full: bool = False, client=default_client) -> dict:
    if full:
        query_file = 'ws/workspace/getWorkspaceFull'
    else:
        query_file = 'ws/workspace/getWorkspace'
    resp = client.make_query(query_file, id=workspace_id)
    ws = resp['data']['workspace']
    if not ws:
        raise WorkspaceNotExists(detail=f'Workspace Not Found or Deleted {workspace_id}')
    return ws


@set_client
def iter_workspaces(company_id: UUID|str, limit: int = None, client=default_client) -> Iterator[dict]:
    yield from iter_query_list(
        'ws/workspace/getWorkspaceList',
        entities_data_key='workspaces',
        variables=dict(companyId=company_id),
        limit=limit,
        client=client
    )


@set_client
def create_workspace(company_id: UUID|str, name: str, description: str = NOTSET, client=default_client) -> str:
    return client.make_query(
        'ws/workspace/createWorkspace',
        name=name,
        companyId=company_id,
        description=description or ""
    )['data']['createWorkspace']['workspaceId']


@set_client
def update_workspace(workspace_id: UUID|str, name: str = NOTSET, description: str = NOTSET, client=default_client) -> bool:
    response = client.make_query(
        'ws/workspace/updateWorkspace',
        id=workspace_id,
        input=dict(
            name=name,
            description=description,
        )

    )
    return response['data']['updateWorkspace']['ok']


@set_client
def find_workspace(company_id: UUID|str, name: str, client=default_client) -> dict:
    filters = deep_tree()
    filters['where']['company']['id']['equalTo'] = str(company_id)
    filters['where']['name']['equalTo'] = name
    resp = client.make_query(
        'ws/workspace/findWorkspace',
        first=1,
        filters=filters,
    )
    if resp['data']['workspaces']['edges']:
        return resp['data']['workspaces']['edges'][0]['node']
    else:
        raise WorkspaceNotExists


@set_client
def delete_workspace(workspace_id: UUID|str, client=default_client) -> bool:
    return client.make_query(
        'ws/workspace/deleteWorkspace',
        id=workspace_id
    )['data']['deleteWorkspace']['ok']


@set_client
def get_workspace_with_revision(workspace_id: UUID|str, revision_id: UUID|str = None, client=default_client) -> dict:
    """
    used current revision if revision_id not set
    """
    if revision_id:
        resp = client.make_query(
            'ws/workspace/getWorkspaceFullCustomRevision',
            workspaceId=str(workspace_id),
            revisionId=str(revision_id)
        )
        workspace = resp['data']['workspace']
        if not workspace:
            raise WorkspaceNotExists

        revision = resp['data']['workspaceRevision']
        if not revision:
            raise RevisionNotExists
    else:
        resp = client.make_query(
            'ws/workspace/getWorkspaceFull',
            workspaceId=str(workspace_id)
        )
        workspace = resp['data']['workspace']
        if not workspace:
            raise WorkspaceNotExists
        revision = resp['data']['workspaceRevisions']['edges'][0]['node']
        if not revision:
            raise RevisionNotExists
    return dict(
        workspace=workspace,
        revision=revision
    )


# revisions
@set_client
def create_revision(
        workspace_id: UUID|str,
        package_release_ids: list[str | UUID],
        set_current: bool = True,
        status: str = 'ready',  # TODO
        layout: dict = NOTSET,
        comment: str = NOTSET,
        metadata: dict = NOTSET,
        client=default_client
    ) -> str:
    return client.make_query(
        'ws/revision/createWorkspaceRevision',
        input= dict(
            workspaceId=workspace_id,
            status=status,
            isCurrent=set_current,
            packageReleaseIds=package_release_ids,
            layout=layout or {},
            comment=comment or '',
            metadata=metadata or {},
        )
    )['data']['createWorkspaceRevision']['workspaceRevisionId']


@set_client
def get_revision(revision_id: UUID|str, client=default_client) -> dict:
    response = client.make_query(
        'ws/revision/getWorkspaceRevision',
        id=str(revision_id),
    )['data']['workspaceRevision']
    if response:
        return response
    else:
        raise RevisionNotExists(detail=f'Workspace revision not found {revision_id}')


@set_client
def update_revision(
        revision_id: UUID|str,
        set_current: bool = NOTSET,
        layout: dict = NOTSET,
        status: str = NOTSET,
        client=default_client
    ) -> str:
    return client.make_query(
        'ws/revision/updateWorkspaceRevision',
        id=revision_id,
        input=dict(
            isCurrent=set_current,
            layout=layout,
            status=status,
        ),
    )['data']['updateWorkspaceRevision']['ok']


@set_client
def iter_revisions(workspace_id: UUID|str, limit: int = None, client=default_client) -> Iterator[dict]:
    yield from iter_query_list(
        'ws/revision/getWorkspaceRevisionList',
        entities_data_key='workspaceRevisions',
        variables=dict(
            workspaceId=workspace_id,
        ),
        limit=limit,
        client=client,
    )


@set_client
def find_revision(
        workspace_id: str = None,
        is_ready: bool = True,
        is_current: bool = False,
        revision_id: UUID|str = None,
        client=default_client
) -> dict|None:
    revision_filter = deep_tree()
    if is_ready:
        revision_filter['where']['status']["equalTo"] = "ready"
    if workspace_id:
        revision_filter['where']['workspace']['id']['equalTo'] = str(workspace_id)
    if is_current:
        revision_filter['where']['isCurrent']['equalTo'] = True
    if revision_id:
        revision_filter['where']['id']['equalTo'] = str(revision_id)
    try:
        return next(iter_query_list(
            'ws/revision/findWorkspaceRevision',
            entities_data_key='workspaceRevisions',
            variables=dict(
                filter=revision_filter,
            ),
            limit=1,
            client=client,
        ))
    except StopIteration:
        raise RevisionNotExists


@set_client
def find_workspace_revision(workspace_id: UUID|str, revision_id: str, client=default_client) -> dict:
    resp = find_revision(workspace_id=workspace_id, revision_id=revision_id, client=client)
    if not resp:
        raise RevisionNotExists
    return resp


@set_client
def get_current_revision(workspace_id: UUID|str, client=default_client) -> dict:
    revision = find_revision(
        workspace_id,
        is_current=True,
        client=client
    )
    if revision:
        return revision
    else:
        raise RevisionNotExists


@set_client
def get_revision_by_project_id(project_id: str, client=default_client) -> dict:
    project = track.get_project(project_id, client=client)
    if not project:
        raise ProjectNotExists
    if not project['workspace']:
        raise ProjectWorkspaceNotSet
    return get_revision_by_workspace_id(project['workspace']['id'], client=client)


@set_client
def get_revision_by_workspace_id(workspace_id: str, client=default_client) -> dict:
    try:
        return find_revision(workspace_id, is_current=True, client=client)
    except RevisionNotExists:
        raise RevisionNotExists('No current revision for workspace {}'.format(workspace_id))


@set_client
def find_workspace_or_revision_by_id(entity_id: UUID|str, client=default_client) -> dict:
    resp = client.make_query(
        'ws/workspace/findWorkspaceOrRevisionById.graphql',
        id=str(entity_id),
    )
    return {
        'revision': resp['data'].get('workspaceRevision'),
        'workspace': resp['data'].get('workspace'),
    }


@set_client
def delete_revision(revision_id: UUID|str, client=default_client) -> bool:
    return client.make_query(
        'ws/revision/deleteWorkspaceRevision',
        id=str(revision_id),
    )


# settings
@set_client
def create_revision_settings(
        revision_id: str|UUID,
        data: dict,
        set_current: bool = True,
        comment: str = '',
        client=default_client
    ) -> str:
    return client.make_query(
        'ws/settings/createSettings',
        workspaceRevisionId=revision_id,
        isCurrent=set_current,
        data=data,
        comment=comment,
    )['data']['createWorkspaceSettings']['workspaceSettingsId']


@set_client
def get_revision_settings(settings_id: UUID|str, client=default_client) -> dict:
    return client.make_query(
        'ws/settings/getSettings',
        revision_id=settings_id
    )['data']['workspaceSettings']


@set_client
def update_revision_settings(settings_id: str|UUID, is_current: bool = NOTSET, comment: str = NOTSET, client=default_client) -> bool:
    input_data = {}
    if is_current is not None:
        input_data['isCurrent'] = is_current
    if comment is not None:
        input_data['comment'] = comment
    return client.make_query(
        'ws/settings/updateSettings',
        id=str(settings_id),
        input=input_data,
    )["data"]["updateWorkspaceSettings"]["ok"]


@set_client
def iter_revision_settings(revision_id: UUID|str, client=default_client) -> Iterator[dict]:
    yield from iter_query_list(
        'ws/settings/getRevisionSettingsList',
        entities_data_key='workspaceSettingses',
        variables=dict(revisionId=revision_id),
        client=client,
    )


@set_client
def get_settings_by_workspace_id(workspace_id: UUID|str, client=default_client) -> dict:
    resp = client.make_query(
        'ws/settings/getSettingsByWorkspaceId',
        workspaceId=workspace_id
    )['data']['workspaceSettingses']['edges']
    if resp:
        return resp[0]['node']
    else:
        raise SettingsRevisionNotExists


@set_client
def get_settings_by_revision_id(revision_id: UUID|str, client=default_client) -> dict:
    resp = client.make_query(
        'ws/settings/getSettingsByRevisionId',
        revisionId=str(revision_id)
    )['data']['workspaceSettingses']['edges']
    if resp:
        return resp[0]['node']
    else:
        raise SettingsRevisionNotExists


@set_client
def get_revision_by_settings_id(settings_id: UUID|str, client=default_client) -> dict:
    # TODO Cache
    settings = get_revision_settings(settings_id, client=client)
    if settings:
        revision_id = settings['workspaceRevisionId']
        return get_revision(revision_id, client=client)
    else:
        raise RevisionNotExists


# find environment
@set_client
def find_environment_by_id(id: str | UUID, client=default_client) -> dict:
    """
    Return list of ids:
    - Workspace id
    - Revision id
    - Settings id
    Return
    - Workspace ID
    - Revision ID|None
    - Settings ID|None
    """
    resp = client.make_query(
        'ws/workspace/findEnvironmentById.graphql',
        id=str(id)
    )
    workspace_id = revision_id = settings_id = None
    entity = None

    # by workspace id
    if resp['data']['revision_by_ws_id']['edges']:
        entity_data = resp['data']['revision_by_ws_id']['edges'][0]['node']
        workspace_id = entity_data['workspaceId']
        revision_id = entity_data['id']
        # settings_id = get_settings_by_revision_id(revision_id)['id']
        entity = 'workspace'

    # by revision id
    elif resp['data']['revision_by_id']['edges']:
        entity_data = resp['data']['revision_by_id']['edges'][0]['node']
        workspace_id = entity_data['workspaceId']
        revision_id = entity_data['id']
        # settings_id = get_settings_by_revision_id(revision_id)['id']
        entity = 'revision'

    # is settings id
    elif resp['data']['by_settings_id']['edges']:
        entity_data = resp['data']['by_settings_id']['edges'][0]['node']
        settings_id = entity_data['id']
        revision_id = entity_data['workspaceRevision']['id']
        workspace_id = entity_data['workspaceRevision']['workspaceId']
        entity = 'settings'

    # py project id
    elif resp['data']['projects']['edges']:
        entity_data = resp['data']['projects']['edges'][0]['node']
        if entity_data['workspaceId']:
            workspace_id = entity_data['workspaceId']
            # revision_id = get_revision_by_workspace_id(workspace_id)['id']
        else:
            revision_id = entity_data['workspaceRevision']['id']
            workspace_id = entity_data['workspaceRevision']['workspaceId']
            # settings_id = get_settings_by_revision_id(revision_id)['id']
        entity = 'project'
    else:
        if resp['data']['by_workspace_id']['edges']:
            raise RevisionNotExists(detail=f'Workspace {id} has no current revision')
        raise WorkspaceNotExists(detail=f'Can not define workspace with provided ID "{id}"')
    return dict(
        workspace_id=workspace_id,
        revision_id=revision_id,
        settings_id=settings_id,
        entity=entity,
    )
