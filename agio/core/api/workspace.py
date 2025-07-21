from typing import Iterator
from uuid import UUID
from . import client
from .utils import NOTSET
from .utils.query_tools import iter_entities


def get_workspace(workspace_id: UUID|str, full: bool = False) -> dict:
    if full:
        query_file = 'ws/workspace/getWorkspaceFull'
    else:
        query_file = 'ws/workspace/getWorkspace'
    resp = client.make_query(query_file, id=workspace_id)
    return resp['data']['workspace']


def iter_workspaces(company_id: UUID, limit: int = None) -> Iterator[dict]:
    yield from iter_entities(
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
        revision = resp['data']['workspaceRevision']
    else:
        resp = client.make_query(
            'ws/workspace/getWorkspaceFull',
            workspaceId=str(workspace_id)
        )
        workspace = resp['data']['workspace']
        revision = resp['data']['workspaceRevisions']['edges'][0]['node']
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
        layout: dict = None,
        comment: str = None,
    ) -> str:
    return client.make_query(
        'ws/revision/createWorkspaceRevision',
        workspaceId=workspace_id,
        packageReleaseIds=package_release_ids,
        isCurrent=set_current,
        status=status,
        layout=layout or {},
        comment=comment or '',
    )['data']['createWorkspaceRevision']['workspaceRevisionId']


def get_revision(revision_id: UUID|str) -> dict:
    return client.make_query(
        'ws/revision/getWorkspaceRevision',
        id=str(revision_id),
    )['data']['workspaceRevision']


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
    yield from iter_entities(
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
        entity_filter['ws'] = {'id': {'equalTo': str(workspace_id)}}
    if is_current:
        entity_filter['isCurrent'] = {'equalTo': True}
    elif workspace_name:
        raise NotImplementedError
        # entity_filter['workspace'] = {'name': {'equalTo': str(workspace_name)}}
    try:
        return next(iter_entities(
            'ws/revision/findWorkspaceRevision',
            entities_data_key='workspaceRevisions',
            variables=dict(
                where=entity_filter,
            ),
            limit=1,
        ))
    except StopIteration:
        return None


def get_current_revision(workspace_id: UUID|str) -> dict|None:
    return find_revision(
        workspace_id,
        is_current=True
    )


def get_revision_by_project_name(project_name: str) -> dict:
    raise NotImplementedError


def get_revision_by_project_id(project_id: str) -> dict:
    raise NotImplementedError


def get_revision_by_workspace_id(workspace_id: str) -> dict:
    return find_revision(workspace_id=workspace_id, is_current=True)


def get_revision_by_workspace_name(workspace_name: str) -> dict:
    return find_revision(workspace_name=workspace_name, is_current=True)


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


def get_revision_settings(revision_id: UUID|str) -> dict:
    return client.make_query(
        'ws/settings/getRevisionSettings',
        revision_id=revision_id
    )['data']['workspaceSettings']


def iter_revision_settings(revision_id: UUID|str) -> Iterator[dict]:
    yield from iter_entities(
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


def get_settings_by_revision_id(revision_id: UUID|str) -> dict:
    resp = client.make_query(
        'ws/settings/getSettingsByRevisionId',
        revisionId=str(revision_id)
    )['data']['workspaceSettingses']['edges']
    if resp:
        return resp[0]['node']
