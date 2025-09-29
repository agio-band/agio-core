from __future__ import annotations
import logging
import os
import re
import shlex
import shutil
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

from agio.core.exceptions import WorkspaceNotExists
from agio.core import pkg
from agio.core.utils import process_utils

# from agio.core.utils import config
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
        self._append_list = defaultdict(list)
        self._prepend_list = defaultdict(list)
        if executable is not None:
            self.set_executable(executable)
        if args is not None:
            self.add_args(*args)
        if env is not None:
            self.set_env(**env)
        if workdir is not None:
            self.set_workdir(workdir)

    def __str__(self):
        return f"{self.executable} {' '.join(self.args or '')}".strip()

    def __repr__(self):
        return f"<LaunchContext {self.executable}>"

    @property
    def executable(self):
        return self._executable.as_posix()

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
        if self._append_list:
            for k, v in self._append_list.items():
                if k in final_envs:
                    final_envs[k] = os.path.pathsep.join((final_envs[k] + os.pathsep.join(v))).strip(os.pathsep)
                else:
                    final_envs[k] = os.pathsep.join(v).strip(os.pathsep)
        if self._prepend_list:
            for k, v in self._prepend_list.items():
                if k in final_envs:
                    final_envs[k] = os.pathsep.join((os.pathsep.join(v), final_envs[k])).strip(os.pathsep)
                else:
                    final_envs[k] = os.pathsep.join(v).strip(os.pathsep)
        return final_envs

    def append_env_path(self, env_name: str, value: str):
        """
        Append path to end
        """
        if env_name == 'PYTHONPATH':
            # specific append function for PYTHONPATH using sitecustomize hook
            # do not use flag -S to keep this customisation
            if not _site_customize_dir.exists():
                raise FileNotFoundError('site customize dir not found: {}'.format(_site_customize_dir))
            res = self.append_env_path('_AGIO_POST_APPEND_PATH', value)
            self.prepend_env_path('PYTHONPATH', _site_customize_dir.as_posix())
            return res
        else:
            if value not in self._append_list[env_name]:
                self._append_list[env_name].append(value)
                return True
            return False

    def prepend_env_path(self, env_name: str, value: str):
        """
        Prepend path to top
        """
        if env_name not in self._prepend_list[env_name]:
            self._prepend_list[env_name].insert(0, value)

    def set_env(self, **kwargs):
        self._envs = {str(k):
                          (os.pathsep.join(v) if isinstance(v, (list, tuple)) else str(v))
                      for k, v in kwargs.items()}

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
    # TODO must by created by installer
    # venvs_path = Path(config.WS.INSTALL_DIR)/'default/bin/python'
    default_exec = os.getenv('AGIO_DEFAULT_WORKSPACE_PY_EXECUTABLE')
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
    ws_manager = None
    if isinstance(workspace, str):
        ws_manager = pkg.AWorkspaceManager.create_from_id(workspace)
    elif isinstance(workspace, pkg.AWorkspaceManager):
        ws_manager = workspace
    elif workspace is None:
        pass # TODO use for full local installation
        # ws_manager = AWorkspaceManager.current()
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
        ws_manager: pkg.AWorkspaceManager|None,
        args: list = None,
        envs: dict = None,
        workdir: str = None,
        **kwargs
    ):
    if ws_manager:
        ctx = ws_manager.get_launch_context()
        ws_manager.install_or_update_if_needed()
        ws_manager.touch()
    else:
        py_exec = kwargs.get('python_executable') or  get_default_env_executable()
        if not py_exec:
            raise WorkspaceNotExists('Executable not set')
        ctx = LaunchContext(py_exec)
    if envs:
        ctx.set_env(**envs)
    if workdir:
        ctx.set_workdir(workdir)
    if args:
        ctx.set_args(args)
    logger.info('Launching command: %s', ' '.join(ctx.command))
    return process_utils.start_process(
        ctx.command,
        env=ctx.envs,
        # clear_envs=['PYTHONPATH'],    # TODO turn back for full installation of workspaces
        workdir=ctx.workdir,
        **kwargs
    )

# @cache_id
# def get_ws_manager_from_args(context_id: str) -> AWorkspaceManager:
#     # is workspace id
#     try:
#         revision = api.workspace.get_revision_by_workspace_id(context_id)
#         return AWorkspaceManager(revision)
#     except NotExistsError:
#         pass
#     # is workspace name
#     # TODO api.workspace.get_revision_by_workspace_label
#     # is revision id
#     try:
#         revision = api.workspace.get_revision(context_id)
#         return AWorkspaceManager(revision)
#     except NotExistsError:
#         pass
#     # is settings id
#     try:
#         revision = api.workspace.get_revision_by_settings_id(context_id)
#         return AWorkspaceManager(revision, settings_revision_id=context_id)
#     except NotExistsError:
#         pass
#     # is project id
#     try:
#         revision = api.workspace.get_revision_by_project_id(context_id)
#         manager = AWorkspaceManager(revision)
#         manager.add_launch_envs({'AGIO_PROJECT_ID': context_id})
#         return manager
#     except NotExistsError:
#         pass
#     raise WorkspaceNotExists


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


