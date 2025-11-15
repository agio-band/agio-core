from typing import Iterator
from uuid import UUID

from . import client
from .utils import NOTSET
from .utils.query_tools import iter_query_list, deep_dict
from ..exceptions import RevisionNotExists, SettingsRevisionNotExists, WorkspaceNotExists, ProjectNotExists, \
    ProjectWorkspaceNotSet
from . import track


def get_workspace(workspace_id: UUID|str, full: bool = False) -> dict:
    if full:
        query_file = 'ws/workspace/getWorkspaceFull'
    else:
        query_file = 'ws/workspace/getWorkspace'
    resp = client.make_query(query_file, id=workspace_id)
    ws = resp['data']['workspace']
    if not ws:
        raise WorkspaceNotExists
    return ws


def iter_workspaces(company_id: UUID|str, limit: int = None) -> Iterator[dict]:
    yield from iter_query_list(
        'ws/workspace/getWorkspaceList',
        entities_data_key='workspaces',
        variables=dict(companyId=company_id),
        limit=limit,
    )


def create_workspace(company_id: UUID|str, name: str, description: str = NOTSET) -> str:
    return client.make_query(
        'ws/workspace/createWorkspace',
        name=name,
        companyId=company_id,
        description=description or ""
    )['data']['createWorkspace']['workspaceId']


def update_workspace(workspace_id: UUID|str, name: str = NOTSET, description: str = NOTSET) -> bool:
    response = client.make_query(
        'ws/workspace/updateWorkspace',
        id=workspace_id,
        input=dict(
            name=name,
            description=description,
        )

    )
    return response['data']['updateWorkspace']['ok']


def find_workspace(company_id: UUID|str, name: str) -> dict:
    filters = deep_dict()
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


def delete_workspace(workspace_id: UUID|str) -> bool:
    return client.make_query(
        'ws/workspace/deleteWorkspace',
        id=workspace_id
    )['data']['deleteWorkspace']['ok']


def get_workspace_with_revision(workspace_id: UUID|str, revision_id: UUID|str = None) -> dict:
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

def create_revision(
        workspace_id: UUID|str,
        package_release_ids: list[str | UUID],
        set_current: bool = True,
        status: str = 'ready',  # TODO
        layout: dict = NOTSET,
        comment: str = NOTSET,
        metadata: dict = NOTSET
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


def get_revision(revision_id: UUID|str) -> dict:
    response = client.make_query(
        'ws/revision/getWorkspaceRevision',
        id=str(revision_id),
    )['data']['workspaceRevision']
    if response:
        return response
    else:
        raise RevisionNotExists


def update_revision(
        revision_id: UUID|str,
        set_current: bool = NOTSET,
        layout: dict = NOTSET,
        status: str = NOTSET
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


def iter_revisions(workspace_id: UUID|str, limit: int = None) -> Iterator[dict]:
    yield from iter_query_list(
        'ws/revision/getWorkspaceRevisionList',
        entities_data_key='workspaceRevisions',
        variables=dict(
            workspaceId=workspace_id,
        ),
        limit=limit,
    )


def find_revision(
        workspace_id: str = None,
        is_ready: bool = True,
        is_current: bool = False,
        revision_id: UUID|str = None,
) -> dict|None:
    revision_filter = deep_dict()
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
        ))
    except StopIteration:
        raise RevisionNotExists


def find_workspace_revision(workspace_id: UUID|str, revision_id: str) -> dict:
    resp = find_revision(workspace_id=workspace_id, revision_id=revision_id)
    if not resp:
        raise RevisionNotExists
    return resp


def get_current_revision(workspace_id: UUID|str) -> dict:
    revision = find_revision(
        workspace_id,
        is_current=True
    )
    if revision:
        return revision
    else:
        raise RevisionNotExists


def get_revision_by_project_id(project_id: str) -> dict:
    project = track.get_project(project_id)
    if not project:
        raise ProjectNotExists
    if not project['workspace']:
        raise ProjectWorkspaceNotSet
    return get_revision_by_workspace_id(project['workspace']['id'])


def get_revision_by_workspace_id(workspace_id: str) -> dict:
    try:
        return find_revision(workspace_id, is_current=True)
    except RevisionNotExists:
        raise RevisionNotExists('No current revision for workspace {}'.format(workspace_id))


def find_workspace_or_revision_by_id(entity_id: UUID|str) -> dict:
    resp = client.make_query(
        'ws/workspace/findWorkspaceOrRevisionById.graphql',
        id=str(entity_id),
    )
    return {
        'revision': resp['data'].get('workspaceRevision'),
        'workspace': resp['data'].get('workspace'),
    }


def delete_revision(revision_id: UUID|str) -> bool:
    return client.make_query(
        'ws/revision/deleteWorkspaceRevision',
        id=str(revision_id),
    )

# settings

def create_revision_settings(
        revision_id: str|UUID,
        data: dict,
        set_current: bool = True,
        comment: str = '',
    ) -> str:
    return client.make_query(
        'ws/settings/createSettings',
        workspaceRevisionId=revision_id,
        isCurrent=set_current,
        data=data,
        comment=comment,
    )['data']['createWorkspaceSettings']['workspaceSettingsId']


def get_revision_settings(settings_id: UUID|str) -> dict:
    return client.make_query(
        'ws/settings/getSettings',
        revision_id=settings_id
    )['data']['workspaceSettings']


def iter_revision_settings(revision_id: UUID|str) -> Iterator[dict]:
    yield from iter_query_list(
        'ws/settings/getRevisionSettingsList',
        entities_data_key='workspaceSettingses',
        variables=dict(revisionId=revision_id)
    )


def get_settings_by_workspace_id(workspace_id: UUID|str) -> dict:
    resp = client.make_query(
        'ws/settings/getSettingsByWorkspaceId',
        workspaceId=workspace_id
    )['data']['workspaceSettingses']['edges']
    if resp:
        return resp[0]['node']
    else:
        raise SettingsRevisionNotExists


def get_settings_by_revision_id(revision_id: UUID|str) -> dict:
    resp = client.make_query(
        'ws/settings/getSettingsByRevisionId',
        revisionId=str(revision_id)
    )['data']['workspaceSettingses']['edges']
    if resp:
        return resp[0]['node']
    else:
        raise SettingsRevisionNotExists


def get_revision_by_settings_id(settings_id: UUID|str) -> dict:
    # TODO Cache
    settings = get_revision_settings(settings_id)
    if settings:
        revision_id = settings['workspaceRevisionId']
        return get_revision(revision_id)
    else:
        raise RevisionNotExists