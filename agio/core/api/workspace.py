from typing import Iterator
from uuid import UUID

from . import client
from .utils import NOTSET
from .utils.query_tools import iter_query_list
from ..exceptions import RevisionNotExists, SettingsRevisionNotExists, WorkspaceNotExists


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


def find_workspace(company_id: UUID|str, name: str = NOTSET) -> dict:
    resp = client.make_query(
        'ws/workspace/findWorkspace',
        first=1,
        where=dict(
            companyId=company_id,
            name=name,
        )
    )
    if resp:
        return resp['data']['workspace']
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
        workspace_name: str = None,
        ready_only: bool = True,
        is_current: bool = False
) -> dict|None:
    entity_filter = {}
    if ready_only:
        entity_filter['status'] = {"equalTo": "ready"}
    if not any([workspace_id, workspace_name]):
        raise ValueError('Workspace id or ws name are required')
    if workspace_id:
        entity_filter['workspace'] = {'id': {'equalTo': str(workspace_id)}}
    if is_current:
        entity_filter['isCurrent'] = {'equalTo': True}
    elif workspace_name:
        raise NotImplementedError
        # entity_filter['workspace'] = {'name': {'equalTo': str(workspace_name)}}
    try:
        return next(iter_query_list(
            'ws/revision/findWorkspaceRevision',
            entities_data_key='workspaceRevisions',
            variables=dict(
                where=entity_filter,
            ),
            limit=1,
        ))
    except StopIteration:
        raise RevisionNotExists


def get_current_revision(workspace_id: UUID|str) -> dict|None:
    revision = find_revision(
        workspace_id,
        is_current=True
    )
    if revision:
        return revision
    else:
        raise RevisionNotExists


def get_revision_by_project_name(project_name: str) -> dict:
    raise NotImplementedError


def get_revision_by_project_id(project_id: str) -> dict:
    raise NotImplementedError


def get_revision_by_workspace_id(workspace_id: str) -> dict:
    return find_revision(workspace_id=workspace_id, is_current=True)


def get_revision_by_workspace_name(workspace_name: str) -> dict:
    raise NotImplementedError
    # return find_revision(workspace_name=workspace_name, is_current=True)


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
    settings = get_revision_settings(settings_id)
    if settings:
        revision_id = settings['workspaceRevisionId']
        return get_revision(revision_id)
    else:
        raise RevisionNotExists