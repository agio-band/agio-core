import os.path
import re
import shlex
import sys
import click
from pathlib import Path
from agio.core.utils.process_utils import start_process
from agio.core.workspace.workspace import AWorkspace


def clear_args(args):
    args_str = ' '.join(args)
    clean = re.sub(r".*?(-ws|--workspace_id)\s+(\w+)\s", "", args_str)
    return shlex.split(clean)


def start_in_workspace(cmd: list[str], workspace_id: str, envs: dict = None, workdir: str = None):
    main_script = os.path.abspath(Path(__file__).joinpath('../__main__.py'))
    workspace_cli_exec = [sys.executable, main_script]
    workspace_envs = (envs or {}) | {'AGIO_CURRENT_WORKSPACE': workspace_id}
    cmd = workspace_cli_exec + cmd[1:]  # TODO check with real binary
    start_process(cmd, envs=workspace_envs, workdir=workdir)
    start_process(cmd, envs=workspace_envs, replace=True, workdir=workdir)


def ensure_workspace(workspace_id: str):
    if not workspace_id:
        click.echo("Workspace ID is not specified.  Please specify it with --workspace_id option or set the AGIO_CURRENT_WORKSPACE environment variable.")
        sys.exit(1)
    ws = AWorkspace(workspace_id)
    if not ws.exists():
        ws.install()


class Env(click.ParamType):
    name = "env_var"

    def convert(self, value, param, ctx):
        if '=' not in value:
            self.fail(f"Invalid environment variable format: {value}.  Expected KEY=VALUE.", param, ctx)
        key, val = value.split('=', 1)
        return key, val

    def get_metavar(self, param):
        return 'KEY=VALUE'
