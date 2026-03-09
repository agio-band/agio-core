import logging

from agio.core.entities import AWorkspace
from agio.core.events import subscribe, AEvent
from agio.core.workspaces import AWorkspaceManager

logger = logging.getLogger(__name__)

@subscribe('agio_apps.start_app.app_created', raise_error=True)
def create_app_workspace(event: AEvent):
    """
    Create personal venv for application. Interpreter is not used, only libs loaded from this venv.
    """
    app: AApplication = event.payload['app']
    # create workspace libs dir
    ws = AWorkspace.current()
    if not ws:
        return
    # create custom workspace
    required_version = app.get_python_version()
    ws_man = AWorkspaceManager.from_workspace(ws, python_version=required_version)
    suffix = f"{app.name}-{app.version}-py{required_version}"
    ws_man.set_suffix(suffix)
    ws_man.install_or_update_if_needed()
    site_packages = ws_man.get_site_packages_path()
    logger.debug("Adding site packages path from workspace: %s", site_packages)
    app.ctx.append_env_path('PYTHONPATH', site_packages)
    app.ctx.append_envs(**ws_man.get_launch_envs())


