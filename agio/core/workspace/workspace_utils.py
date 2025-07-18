from uuid import UUID

from agio.core import api


def create_workspace(
        name: str,
        description: str,
        label: str = None,  # TODO
        company_id: str = None
) -> str:
    company_id = company_id or api.desk.get_current_company()['id']
    return api.workspace.create_workspace(
        company_id=company_id,
        name=name,
        description=description or ''
    )


def get_workspace(workspace_id: str) -> dict:
    return api.workspace.get_workspace_with_revision(workspace_id)

def set_workspace_package_list(
        workspace_id: str,
        packages: list,
        set_current: bool = False,
        comment: str = None
):
    # collect releases
    release_ids = []
    for package in packages:
        if isinstance(package, dict):
            release = api.package.get_package_release_by_name_and_version(
                package['name'], package['version']
            )
            if not release:
                raise Exception(f'Package release {package["name"]}:{package["version"]} not found')
            release_ids.append(release['id'])
        elif isinstance(package, str):
            try:
                UUID(package)
            except ValueError:
                raise Exception(f'Wrong UUID value for ID: {package}')
            release = api.package.get_package_release(package)
            if not release:
                raise Exception(f'Package release {package} not found')
            release_ids.append(release['id'])
        else:
            raise Exception(f'Wrong type for package: {package}')
    # create revision
    if not release_ids:
        raise Exception(f'No package releases found')
    return api.workspace.create_revision(
        workspace_id=workspace_id,
        package_release_ids=release_ids,
        set_current=set_current,
        status='ready', # TODO change to "sync"
        # layout={},
        comment=comment,
    )


def set_revision_layout(
        revision_id: str,
        layout: dict,
):
    return api.workspace.update_revision(
        revision_id=revision_id,
        layout=layout
    )


def set_workspace_settings(
        workspace_id: str,
        settings: dict,
):
    revision = api.workspace.get_current_revision(workspace_id)
    return set_revision_settings(revision['id'], settings)


def set_revision_settings(
        revision_id: str,
        settings_data: dict,
        set_current: bool = False,
):
    return api.workspace.create_revision_settings(
        revision_id,
        settings_data,
        set_current=set_current
    )


def delete_workspace(
        workspace_id: str,
):
    return api.workspace.delete_workspace(workspace_id)


def set_current_revision(
        workspace_id: str,
        revision_id: str,
):
    revision_list = [rev['id'] for rev in api.workspace.iter_revisions(workspace_id)]
    if revision_id not in revision_list:
        raise Exception(f'Revision {revision_id} not found in workspace {workspace_id}')
    return api.workspace.update_revision(revision_id, set_current=True)
