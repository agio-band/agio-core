import re
import shlex
import sys
import click
from pathlib import Path
from agio.core.utils.process import start_process


def clear_args(args):
    args_str = ' '.join(args)
    clean = re.sub(r".*?(-ws|--workspace_id)\s+(\w+)\s", "", args_str)
    return shlex.split(clean)


def start_in_workspace(cmd: list[str], workspace_id: str, envs: dict = None, workdir: str = None):
    main_script = Path(__file__).joinpath('../../../__main__.py').absolute().as_posix()
    workspace_cli_exec = [sys.executable, main_script]
    workspace_envs = (envs or {}) | {'AGIO_WORKSPACE_ID': workspace_id}
    cmd = workspace_cli_exec + cmd
    start_process(cmd, envs=workspace_envs, replace=True, workdir=workdir)


class Env(click.ParamType):
    name = "env_var"

    def convert(self, value, param, ctx):
        if '=' not in value:
            self.fail(f"Invalid environment variable format: {value}.  Expected KEY=VALUE.", param, ctx)
        key, val = value.split('=', 1)
        return key, val

    def get_metavar(self, param):
        return 'KEY=VALUE'
