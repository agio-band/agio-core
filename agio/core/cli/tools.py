import logging
import os.path
import re
import shlex
import sys

import click

from agio.core import api
from agio.core.exceptions import WorkspaceNotExists, EntityNotExists
from agio.core.utils.process_utils import start_process
from agio.core.pkg.workspace import AWorkspace, AWorkspaceManager

logger = logging.getLogger(__name__)

def clear_args(args):
    args_str = ' '.join(args)
    clean = re.sub(r".*?(-ws|--workspace_id)\s+(\w+)\s", "", args_str)
    return shlex.split(clean)


def start_in_workspace(workspace: AWorkspaceManager, cmd: list[str], envs: dict = None, workdir: str = None):
    # find py executable
    py_exec = workspace.get_pyexecutable()
    # find cli script
    workspace_cli_exec = [py_exec, '-m', 'agio']
    cmd = workspace_cli_exec + cmd[1:]  # TODO check with real binary
    workspace.install_or_update_if_needed()
    envs = {**(envs or {}), **workspace.get_launch_envs()}
    start_process(cmd, envs=envs, clear_envs=['PYTHONPATH'], replace=True, workdir=workdir)


def ensure_workspace(revision_id: str = None):
    ws = AWorkspaceManager(revision_id)
    if not ws.need_to_reinstall():
        ws.install()


def get_workspace_from_args(project=None, workspace=None):
    if workspace:

        for func, extra_args in (
                (api.workspace.get_revision_by_workspace_id, None),
                # (api.workspace.get_revision_by_workspace_name, None),
                (api.workspace.get_revision, None),
                (api.workspace.get_revision_by_settings_id, {'settings_revision_id': workspace})
            ):
            try:
                revision = func(workspace)
                if not revision:
                    continue
                return AWorkspaceManager(revision, **(extra_args or {}))
            except EntityNotExists:
                continue
        raise WorkspaceNotExists
    elif project:
        # TODO
        revision = (api.workspace.get_revision_by_project_id(project) or
                    api.workspace.get_revision_by_project_name(project))
        if revision:
            return AWorkspaceManager(revision)
        raise Exception('Project does not exist')
    else:
        return


class Env(click.ParamType):
    name = "env_var"

    def convert(self, value, param, ctx):
        if '=' not in value:
            self.fail(f"Invalid environment variable format: {value}.  Expected KEY=VALUE.", param, ctx)
        key, val = value.split('=', 1)
        return key, val

    def get_metavar(self, param):
        return 'KEY=VALUE'
