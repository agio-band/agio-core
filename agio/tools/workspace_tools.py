from agio.core.api.utils import NOTSET
from agio.core.entities import AWorkspace, AWorkspaceRevision, APackageRelease
from agio.core.entities.company import ACompany
from agio.core.exceptions import WorkspaceNotExists
from agio.core.settings.settings_hub import WorkspaceSettingsHub
from agio.tools.packaging_tools import collect_packages_to_install


def create_workspace(workspace_name: str,
                     company: ACompany|str,
                     package_list: list[APackageRelease|str],
                     settings_data: dict|WorkspaceSettingsHub,
                     description: str = None,
                     comment: str = None,
                     ) -> AWorkspaceRevision:
    # check company
    if isinstance(company, ACompany):
        company = company.id
    # check workspace exists
    try:
        if AWorkspace.find(company_id=company, name=workspace_name):
            raise NameError(f"Workspace name {workspace_name} already exists")
    except WorkspaceNotExists:
        pass

    # check package_list
    package_list = collect_packages_to_install(package_list)
    # check settings
    _ = WorkspaceSettingsHub(settings_data)

    # create workspace
    ws = AWorkspace.create(
        company_id=company,
        name=workspace_name,
        description=description or NOTSET,
    )
    revision = AWorkspaceRevision.create(
        workspace_id=ws.id,
        package_releases=package_list,
        set_current=True,
        comment=comment,
    )
    return revision



def update_workspace(workspace: AWorkspace|str,
                     package_list: list[APackageRelease|str],
                     settings_data: dict|WorkspaceSettingsHub) -> AWorkspaceRevision:
    pass
