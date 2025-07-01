from typing import Iterator
from uuid import UUID
from . import client
from .utils import NOTSET
from .utils.query_tools import iter_entities


def get_workspace(workspace_id: UUID|str, full: bool = False) -> dict:
    if full:
        query_file = 'workspace/ws/getWorkspaceFull'
    else:
        query_file = 'workspace/ws/getWorkspace'
    resp = client.make_query(query_file, id=workspace_id)
    return resp['data']['workspace']


# def get_workspace_list(company_id: UUID, items_per_page: int = 10,  after: str = None) -> dict:
#     response = client.make_query(
#         'workspace/ws/getWorkspaceList',
#         companyId=company_id,
#         first=items_per_page,
#         afterCursor=after,
#     )
#     return dict(
#         data=[x['node'] for x in response['data']['workspaces']['edges']],
#         pageInfo=response['data']['workspaces']['pageInfo'],
#     )

def iter_workspaces(company_id: UUID, limit: int = None) -> Iterator[dict]:
    yield from iter_entities(
        'workspace/ws/getWorkspaceList',
        entities_data_key='workspaces',
        variables=dict(companyId=company_id),
        limit=limit,
    )


def create_workspace(company_id: UUID|str, name: str, description: str = NOTSET) -> str:
    return client.make_query(
        'workspace/ws/createWorkspace',
        name=name,
        companyId=company_id,
        description=description or ""
    )['data']['createWorkspace']['workspaceId']


def update_workspace(workspace_id: UUID|str, name: str = NOTSET, description: str = NOTSET) -> bool:
    response = client.make_query(
        'workspace/ws/updateWorkspace',
        id=workspace_id,
        input=dict(
            name=name,
            description=description,
        )

    )
    return response['data']['updateWorkspace']['ok']


def delete_workspace(workspace_id: UUID|str) -> bool:
    return client.make_query(
        'workspace/ws/deleteWorkspace',
        id=workspace_id
    )['data']['deleteWorkspace']['ok']


# revisions

def create_revision(
        workspace_id: UUID|str,
        package_release_ids: list[str | UUID],
        set_current: bool = True,
        status: str = 'ready',  # TODO
        layout: dict = None,
        comment: str = '',
    ) -> str:
    return client.make_query(
        'workspace/revision/createWorkspaceRevision',
        workspaceId=workspace_id,
        packageReleaseIds=package_release_ids,
        isCurrent=set_current,
        status=status,
        layout=layout or {},
        comment=comment,
    )['data']['createWorkspaceRevision']['workspaceRevisionId']


def update_revision(
        revision_id: UUID|str,
        set_current: bool = NOTSET,
        layout: dict = NOTSET,
        status: str = NOTSET
    ) -> str:
    return client.make_query(
        'workspace/revision/updateWorkspaceRevision',
        id=revision_id,
        input=dict(
            isCurrent=set_current,
            layout=layout,
            status=status,
        ),
    )['data']['updateWorkspaceRevision']['ok']


# def get_revision_list(
#         workspace_id: UUID|str,
#         items_per_page: int = 10,
#         after: str = None
#     ):
#     return [x['node'] for x in client.make_query(
#         'workspace/revision/getWorkspaceRevisionList',
#         workspaceId=workspace_id,
#         first=items_per_page,
#         afterCursor=after,
#     )['data']['workspaceRevisions']['edges']]


def iter_revisions(workspace_id: UUID|str, limit: int = None) -> Iterator[dict]:
    yield from iter_entities(
        'workspace/revision/getWorkspaceRevisionList',
        entities_data_key='workspaceRevisions',
        variables=dict(workspaceId=workspace_id),
        limit=limit,
    )


# settings

def create_revision_settings(
        revision_id: str|UUID,
        data: dict,
        set_current: bool = True,
        comment: str = '',
    ):
    return client.make_query(
        'workspace/settings/createRevisionSettings',
        workspaceRevisionId=revision_id,
        isCurrent=set_current,
        data=data,
        comment=comment,
    )['data']['createWorkspaceSettings']['workspaceSettingsId']


def get_revision_settings(revision_id: UUID|str) -> dict:
    return client.make_query(
        'workspace/settings/getRevisionSettings',
        revision_id=revision_id
    )['data']['workspaceSettings']


# def get_revision_settings_list(
#         revision_id: UUID|str,
#         items_per_page: int = 10,
#         after: str = None,
#     ):
#     return client.make_query(
#         'workspace/settings/getRevisionSettingsList',
#         revisionId=revision_id,
#         first=items_per_page,
#         afterCursor=after,
#     )['data']['workspaceSettings']['revisionSettings']


def iter_revision_settings(revision_id: UUID|str) -> Iterator[dict]:
    yield from iter_entities(
        'workspace/settings/getRevisionSettingsList',
        entities_data_key='workspaceSettingses',
        variables=dict(revisionId=revision_id)
    )