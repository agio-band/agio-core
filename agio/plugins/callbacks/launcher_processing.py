import logging

from agio.apps.exceptions import ApplicationNotFoundError
from agio.apps.launcher import AApplicationLauncher
from agio.core.entities import AWorkspace
from agio.core.events import subscribe, AEvent
from agio.core.exceptions import WorkspaceNotDefined
from agio.core.workspaces import AWorkspaceManager

logger = logging.getLogger(__name__)


@subscribe('agio_core.start_app.app_created', raise_error=True)
def create_app_workspace(event: AEvent):
    """
    Create personal venv for application. Interpreter is not used, only libs loaded from this venv.
    """
    app: AApplicationLauncher = event.payload['app']
    # create workspace libs dir
    try:
        ws = AWorkspace.current()
    except WorkspaceNotDefined:
        return
    # create custom workspace for app
    required_version = app.get_python_version()
    try:
        # try to get app interpreter
        py_app = app.switch_mode('python')
        venv_manager_python = py_app.get_executable()
    except ApplicationNotFoundError:
        # use interpreter with savme version
        venv_manager_python = required_version
    # TODO: update for apps without py interpreter
    ws_man = AWorkspaceManager.from_workspace(ws, python_version=venv_manager_python)
    suffix = f"{app.name}-{app.version}-py{required_version}"
    ws_man.set_suffix(suffix)
    ws_man.install_or_update_if_needed()
    site_packages = ws_man.get_site_packages_path()
    logger.debug("Adding site packages path from workspace: %s", site_packages)
    app.ctx.append_env_path('PYTHONPATH', site_packages)
    app.ctx.append_envs(**ws_man.get_launch_envs())
