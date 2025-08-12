import os
import re
import shlex

from agio.core import api
from agio.core.exceptions import WorkspaceNotExists, NotExistsError
from agio.core.pkg import AWorkspaceManager
from agio.core.utils import process_utils
# from agio.core.utils import config


def get_default_env_executable():
    # TODO must by created by installer
    # venvs_path = Path(config.WS.INSTALL_DIR)/'default/bin/python'
    default_exec = os.getenv('AGIO_DEFAULT_WORKSPACE_PY_EXECUTABLE')
    if not default_exec:
        raise WorkspaceNotExists('AGIO_DEFAULT_WORKSPACE_PY_EXECUTABLE not set')
    return default_exec


def exec_agio_command(
        args: list,
        workspace: str|AWorkspaceManager = None,
        envs: dict = None,
        workdir: str = None,
        **kwargs
    ):
    if isinstance(workspace, str):
        ws_manager = get_launch_context_from_args(workspace)
    elif isinstance(workspace, AWorkspaceManager):
        ws_manager = workspace
    elif workspace is None:
        ws_manager = AWorkspaceManager.current()
    else:
        raise TypeError("Workspace must be either a string or AWorkspaceManager.")
    start_in_workspace(
        command=['-m', 'agio'] + args,
        ws_manager=ws_manager,
        envs=envs,
        workdir=workdir,
        **kwargs
    )


def start_in_workspace(
        command,
        ws_manager: AWorkspaceManager|None,
        envs: dict = None,
        workdir: str = None,
        **kwargs
    ):
    if ws_manager:
        py_exec = ws_manager.get_pyexecutable()
        ws_manager.install_or_update_if_needed()
        ws_manager.touch()
        ws_envs = ws_manager.get_launch_envs()
    else:
        py_exec = get_default_env_executable()
        ws_envs = {}
    cmd = [py_exec] + command
    envs = {**(envs or {}), **ws_envs}
    return process_utils.start_process(
        cmd, envs=envs,
        # clear_envs=['PYTHONPATH'],    # TODO turn back for full installation of workspaces
        workdir=workdir,
        **kwargs
    )


def get_launch_context_from_args(context_id: str) -> AWorkspaceManager:
    # is workspace id
    try:
        revision = api.workspace.get_revision_by_workspace_id(context_id)
        return AWorkspaceManager(revision)
    except NotExistsError:
        pass
    # is workspace name
    # TODO api.workspace.get_revision_by_workspace_label
    # is revision id
    try:
        revision = api.workspace.get_revision(context_id)
        return AWorkspaceManager(revision)
    except NotExistsError:
        pass
    # is settings id
    try:
        revision = api.workspace.get_revision_by_settings_id(context_id)
        return AWorkspaceManager(revision, settings_revision_id=context_id)
    except NotExistsError:
        pass
    # is project id
    try:
        revision = api.workspace.get_revision_by_project_id(context_id)
        manager = AWorkspaceManager(revision)
        manager.add_launch_envs({'AGIO_PROJECT_ID': context_id})
        return manager
    except NotExistsError:
        pass
    raise WorkspaceNotExists


def clear_args(args):
    args_str = ' '.join(args)
    clean = re.sub(r".*?(-w|--workspace|-p|--project)\s+(\w+)\s", "", args_str)
    return shlex.split(clean)
