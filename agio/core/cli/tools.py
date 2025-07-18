import logging
import os.path
import re
import shlex
import sys

import click

from agio.core import api
from agio.core.utils.process_utils import start_process
from agio.core.workspace.workspace import AWorkspace

logger = logging.getLogger(__name__)

def clear_args(args):
    args_str = ' '.join(args)
    clean = re.sub(r".*?(-ws|--workspace_id)\s+(\w+)\s", "", args_str)
    return shlex.split(clean)


def start_in_workspace(workspace: AWorkspace, cmd: list[str], envs: dict = None, workdir: str = None):
    # find py executable
    py_exec = workspace.get_pyexecutable()
    # find cli script
    workspace_cli_exec = [py_exec, '-m', 'agio']
    cmd = workspace_cli_exec + cmd[1:]  # TODO check with real binary
    workspace.install_or_update_if_needed()
    envs = {**(envs or {}), **workspace.get_launch_envs()}
    start_process(cmd, envs=envs, clear_envs=['PYTHONPATH'], replace=True, workdir=workdir)


def ensure_workspace(workspace_id: str, revision_id: str = None):
    if not workspace_id:
        click.echo("Workspace ID is not specified.  Please specify it with --workspace_id option or set the AGIO_WORKSPACE_ID environment variable.")
        sys.exit(1)
    ws = AWorkspace(workspace_id, revision_id)
    if not ws.exists(): # TODO FIX IT
        ws.install()


def get_workspace_from_args(**kwargs):
    project_context = {k: v for k, v in kwargs.items() if k in ('project_name', 'project_id') and v is not None}
    workspace_context = {k: v for k, v in kwargs.items() if
                         k in ('workspace_id', 'workspace_name', 'revision_id', 'settings_id') and v is not None}
    if workspace_context:
        if len(workspace_context) != 1:
            raise ValueError('Mixing of workspace arguments is disabled.')
        if 'workspace_id' in workspace_context:
            revision = api.workspace.get_revision_by_workspace_id(workspace_context['workspace_id'])
        elif 'revision_id' in workspace_context:
            revision = api.workspace.get_revision(workspace_context['revision_id'])
        else: # settings_id
            revision = api.workspace.get_revision(workspace_context['revision_id'])
    elif project_context:
        if 'project_id' in project_context:
            revision = api.workspace.get_revision_by_project_id(project_context['project_id'])
        else:
            revision = api.workspace.get_revision_by_project_name(project_context['project_name'])
    else:
        return
    return AWorkspace(revision['workspaceId'], revision['id'])


class Env(click.ParamType):
    name = "env_var"

    def convert(self, value, param, ctx):
        if '=' not in value:
            self.fail(f"Invalid environment variable format: {value}.  Expected KEY=VALUE.", param, ctx)
        key, val = value.split('=', 1)
        return key, val

    def get_metavar(self, param):
        return 'KEY=VALUE'
