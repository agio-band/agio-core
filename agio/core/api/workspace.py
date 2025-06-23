from uuid import UUID
from . import client


def get_workspace(workspace_id: UUID|str, full: bool = False) -> dict:
    if full:
        query_file = 'workspace/ws/getWorkspaceFull'
    else:
        query_file = 'workspace/ws/getWorkspace'
    resp = client.make_query(query_file, id=workspace_id)
    return resp['data']['workspace']


def get_workspace_list(company_id: UUID, items_per_page: int = 10,  after: str = None) -> dict:
    response = client.make_query(
        'workspace/ws/getWorkspaceList',
        companyId=company_id,
        first=items_per_page,
        afterCursor=after,
    )
    return dict(
        data=[x['node'] for x in response['data']['workspaces']['edges']],
        pageInfo=response['data']['workspaces']['pageInfo'],
    )


def create_workspace(company_id: UUID|str, name: str, description: str = None) -> str:
    return client.make_query(
        'workspace/ws/createWorkspace',
        name=name,
        companyId=company_id,
        description=description or ""
    )['data']['createWorkspace']['workspaceId']


def update_workspace(workspace_id: UUID|str, name: str = None, description: str = None) -> bool:
    response = client.make_query(
        'workspace/ws/updateWorkspace',
        id=workspace_id,
        name=name,
        description=description,
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
        package_release_ids: list[str | UUID] = None,
        set_current: bool = None,
        status: str = None,
        layout: dict = None,
        comment: str = None,
    ) -> str:
    return client.make_query(
        'workspace/revision/createWorkspaceRevision',
        workspaceId=workspace_id,
        packageReleaseIds=package_release_ids,
        isCurrent=set_current,
        status=status,
        layout=layout,
        comment=comment,
    )['data']['createWorkspaceRevision']['workspaceRevisionId']


def update_revision(
        revision_id: UUID|str,
        set_current: bool = None,
        layout: dict = None,
        status: str = None
    ) -> str:
    return client.make_query(
        'workspace/revision/updateWorkspaceRevision',
        id=revision_id,
        isCurrent=set_current,
        layout=layout,
        status=status,
    )['data']['updateWorkspaceRevision']['ok']


def get_revision_list(
        workspace_id: UUID|str,
    ):
    pass


# settings

def set_revision_settings(
        revision_id: str|UUID,
        data: dict,
        set_current: bool = True,
        comment: str = None,
    ):
    return client.make_query(
        'workspace/settings/createWorkspaceRevisionSettings',
        workspaceRevisionId=revision_id,
        data=data,
        isCurrent=set_current,
        comment=comment,
    )['data']#['workspaceSettingsId']


def get_revision_settings(revision_id: UUID) -> dict:
    return client.make_query(
        'workspace/settings/getWorkspaceRevisionSettings',
        id=revision_id
    )


def get_revision_settings_list(
        revision_id: UUID,
        items_per_page: int = 10,
        after: str = None,
    ):
    ...


