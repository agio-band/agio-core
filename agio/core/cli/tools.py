import os
import re
import shlex
import sys

from agio.core.utils.process_utils import start_process


def clear_args(args):
    args_str = ' '.join(args)
    clean = re.sub(r".*?(-ws|--workspace_id)\s+(\w+)\s", "", args_str)
    return shlex.split(clean)


def start_in_workspace(cmd: list[str], workspace_id: str, envs: dict = None, workdir: str = None):
    workspace_cli_exec = [sys.executable, '/home/paul/pw-storage/dev/work/agio/packages/agio-core/agio/core/cli/__main__.py']
    workspace_envs = (envs or {}) | {'AGIO_WORKSPACE_ID': workspace_id}
    cmd = workspace_cli_exec + cmd
    # print('PID 1', os.getpid())
    start_process(cmd, envs=workspace_envs, replace=True, workdir=workdir)
