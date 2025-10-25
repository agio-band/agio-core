from __future__ import annotations

import logging
import os
import re
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

from agio.core import pkg
from agio.core.exceptions import WorkspaceNotExists
from agio.core.utils import process_utils, app_dirs
from agio.core.utils.pkg_manager import get_package_manager_class

logger = logging.getLogger(__name__)


_site_customize_dir = Path(__file__).resolve().parent / '_import_tools'


class LaunchContext:
    """
    A general class for configuring the startup of any process
    """
    def __init__(self, executable: str|Path, args: list[str] = None, env: dict = None,
                 workdir: str = None, inherit_system_envs: bool = True):
        self._executable = None
        self._args = None
        self._envs = None
        self._workdir = None
        self._inherit_system_envs = inherit_system_envs
        if executable is not None:
            self.set_executable(executable)
        if args is not None:
            self.add_args(*args)
        if env is not None:
            self.append_envs(**env)
        if workdir is not None:
            self.set_workdir(workdir)

    def __str__(self):
        return f"{self.executable} {' '.join(self.args or '')}".strip()

    def __repr__(self):
        return f"<LaunchContext {self.executable}>"

    @property
    def executable(self):
        return Path(self._executable).as_posix()

    def set_executable(self, value):
        if not value:
            raise ValueError("The executable cannot be empty")
        _value, *args = shlex.split(value, posix=os.name!='nt')
        _value = Path(value).expanduser()
        if not _value.is_absolute():
            abs_path = shutil.which(_value.as_posix())
            if not abs_path:
                raise FileNotFoundError(f"The executable at {value} could not be found")
            _value = Path(abs_path)
        if not _value.exists():
            raise FileNotFoundError(value)
        if args:
            self._args.extend(args)
        self._executable = _value

    @property
    def args(self) -> list[str]:
        return self._args or []

    @args.setter
    def args(self, values: list[str]):
        self._args = list(str(v) for v in values)

    def add_args(self, *args: str):
        if self._args is not None:
            self._args.extend(args)
        else:
            self._args = list(args)

    @property
    def envs(self) -> dict[str, str]:
        system_envs = os.environ.copy() if self._inherit_system_envs else {}
        final_envs = system_envs.copy()
        if self._envs:
            final_envs.update(self._envs)
        return final_envs

    def append_env_path(self, env_name: str, value: str):
        """
        Append path to end of sys.path
        """
        logger.debug(f"Appending path env {env_name}={value}")
        if env_name == 'PYTHONPATH':
            # specific append function for PYTHONPATH using sitecustomize hook
            # do not use flag -S to keep this customisation
            if not _site_customize_dir.exists():
                raise FileNotFoundError('site customize dir not found: {}'.format(_site_customize_dir))
            res = self.append_env_path('__AGIO_POST_APPEND_PATH__', value)
            self.prepend_env_path('PYTHONPATH', _site_customize_dir.as_posix())
            return res
        else:
            path_list = self._envs.get(env_name, '').split(os.pathsep)
            if value not in path_list:
                path_list.append(value)
                self._envs[env_name] = os.pathsep.join(path_list).strip(os.pathsep)
                return True
            return False

    def prepend_env_path(self, env_name: str, value: str):
        """
        Prepend path to top of sys.path
        """
        logger.debug(f"Prepending path env {env_name}={value}")
        path_list = self._envs.get(env_name, '').split(os.pathsep)
        if value not in path_list:
            path_list.insert(0, value)
            self._envs[env_name] = os.pathsep.join(path_list).strip(os.pathsep)
            return True
        return False

    def set_environ(self, **kwargs):
        """
        Replace all environment variables
        """
        self._envs = {
            str(k): (os.pathsep.join(v) if isinstance(v, (list, tuple)) else str(v))
            for k, v in kwargs.items()
        }

    def append_envs(self, **kwargs):
        """
        You can set multipath value as list or tuple
        """
        self._envs = self._envs or {}
        for k, v in kwargs.items():
            if isinstance(v, (list, tuple)):
                v = os.pathsep.join(v)
            self._envs[k] = v

    @property
    def workdir(self) -> str|None:
        if self._workdir is None:
            return None
        return self._workdir.as_posix()

    def set_workdir(self, value):
        if value is None:
            self._workdir = None
        value = Path(value).expanduser().absolute()
        if not Path(value).exists():
            raise FileNotFoundError(f'Path not exists: {value}')
        self._workdir = value

    @property
    def command(self) -> list[str]:
        if not self._executable:
            raise ValueError('Executable not provided')
        cmd = [self.executable]
        if self.args:
            cmd.extend(self.args)
        return cmd

    def validate(self):
        if not self._executable:
            raise ValueError('Executable not provided')
        if self._workdir is not None:
            if not Path(self._workdir).exists():
                raise FileNotFoundError('Workdir does not exist')

    def to_dict(self) -> dict:
        return dict(
            executable=self.executable,
            args=self.args,
            command=self.command,
            envs=self.envs,
            workdir=self.workdir,
        )


def get_default_env_executable():
    default_exec = os.getenv('AGIO_DEFAULT_WORKSPACE_PY_EXECUTABLE')
    if default_exec:
        return default_exec
    default_venv = app_dirs.get_default_env_dir()
    manager  = get_package_manager_class()
    default_exec = manager(default_venv).python_executable
    if not default_exec:
        raise WorkspaceNotExists('AGIO_DEFAULT_WORKSPACE_PY_EXECUTABLE not set')
    return default_exec


def exec_agio_command(
        args: list,
        workspace: str|pkg.AWorkspaceManager = None,
        envs: dict = None,
        workdir: str = None,
        **kwargs
    ):
    """
    Launching agio command

    Example usage:
    >>> cmd = ['mycmd', '--arg', 1, '--key', 2]
    >>> exec_agio_command(cmd, 'some-uuid-value')
    Command will be converted to

    `agio -w [ws.id] mycmd --arg 1 --key 2`

    Commands plugin must be registered
    """
    ws_manager = None
    if not os.getenv('AGIO_FORCE_DEFAULT_WORKSPACE'):  # start in default env always (for beta version)
        if isinstance(workspace, str):
            ws_manager = pkg.AWorkspaceManager.create_from_id(workspace)
        elif isinstance(workspace, pkg.AWorkspaceManager):
            ws_manager = workspace
        elif workspace is None:
            ws_manager = pkg.AWorkspaceManager.current()
        else:
            raise TypeError("Workspace must be either a string or AWorkspaceManager.")
    return start_in_workspace(
        ws_manager=ws_manager,
        args=['-m', 'agio'] + args,
        envs=envs,
        workdir=workdir,
        **kwargs
    )


def start_in_workspace(
        ws_manager: pkg.AWorkspaceManager|str|None,
        args: list = None,
        envs: dict = None,
        workdir: str = None,
        **kwargs
    ):
    if os.getenv('AGIO_FORCE_DEFAULT_WORKSPACE'):   # start in default env always (for beta version)
        ws_manager = None
    if isinstance(ws_manager, str):
        ws_manager = pkg.AWorkspaceManager.create_from_id(ws_manager)
    if ws_manager:
        ctx: LaunchContext = ws_manager.get_launch_context()
        ws_manager.install_or_update_if_needed()
        ws_manager.touch()
    else:
        py_exec = kwargs.get('python_executable') or  get_default_env_executable()
        if not py_exec:
            raise WorkspaceNotExists('Executable not set')
        ctx = LaunchContext(py_exec)
    if envs:
        ctx.append_envs(**envs)
    if workdir:
        ctx.set_workdir(workdir)
    if args:
        ctx.add_args(*args)
    if not Path(ctx.executable).exists():
        raise FileNotFoundError(f'Executable not found {ctx.executable}')
    logger.info('Launching command: %s', ' '.join(ctx.command))
    return process_utils.start_process(
        ctx.command,
        env=ctx.envs,
        clear_env=['PYTHONPATH'],    # TODO turn back for full installation of workspaces
        workdir=ctx.workdir,
        **kwargs
    )


def clear_args(args):
    args_str = ' '.join(args)
    clean = re.sub(r".*?(-w|--workspace|-p|--project)\s+(\w+)\s", "", args_str)
    return shlex.split(clean)


def start_file(path: str):
    """
    Open file or folder using native app
    """
    path = Path(path).expanduser().resolve()

    if not path.exists():
        raise FileNotFoundError(f"Path not found: {path}")

    if sys.platform.startswith("win"):
        os.startfile(path)
    elif sys.platform.startswith("darwin"):
        subprocess.run(["open", str(path)])
    else:  # Linux, BSD, etc.
        subprocess.run(["xdg-open", str(path)])


