import logging
import os
import shlex
import sys
import signal
import subprocess
import argparse
from pathlib import Path
from typing import Iterable, Callable
from agio.tools import custom_pipe

logger = logging.getLogger(__name__)

IS_WIN32 = sys.platform == "win32"

def terminate_child(proc):
    """
    Terminates a process and its whole process group (or job).
    """
    if IS_WIN32:
        # /F: Force termination
        # /T: Terminate the specified process and any child processes started by it
        subprocess.call(["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        except ProcessLookupError:
            pass # Process already dead



def start_process(
        command: list[str] | tuple[str] | str,
        env: dict = None,
        clear_env: list = None,
        detached: bool = False,
        replace: bool = False,
        new_console: bool = False,
        non_blocking: bool = False,
        output_file=None,
        workdir: str = None,
        get_output: bool = False,
        use_custom_pipe: bool = False,
        exit_on_done=False,
        **kwargs
):
    """
    Universal function to start a process with different modes.

    Automatically terminates child process if parent is killed (when not detached).
    Propagates exit code from child to parent if the child crashes.
    """
    if get_output and use_custom_pipe:
        raise Exception("open_pipe and get_output are mutually exclusive")
    if detached and use_custom_pipe:
        raise Exception('Argument open_pipe cannot be used with detached=True')
    if use_custom_pipe and replace:
        raise Exception('Argument open_pipe cannot be used with replace=True')
    if detached and replace:
        raise Exception('Argument replace cannot be used with detached=True')
    if replace and get_output:
        raise Exception('Argument replace cannot be used with get_output=True')
    new_env = os.environ.copy()
    if clear_env:
        for env_name in clear_env:
            new_env.pop(env_name, None)
    if env:
        new_env.update(env)
    if workdir:
        workdir = os.path.abspath(os.path.expanduser(workdir))
        if not os.path.isdir(workdir):
            print(f"Error: Working directory '{workdir}' does not exist.")
            sys.exit(1)
    if isinstance(command, Iterable):
        command = list(map(str, command))
    if replace:
        if isinstance(command, str):
            command = shlex.split(command)
        executable = command[0]
        if workdir:
            try:
                os.chdir(workdir)
            except OSError as e:
                print(f"Error changing directory: {e}")
                exit(1)
        command = [shlex.quote(x).replace("'", '"') for x in command]   # fix quotes for Windows os
        if os.path.isabs(executable):
            os.execve(executable, command, new_env)
        else:
            os.execvpe(executable, command, new_env)

    creationflags = 0
    stdin = None
    start_new_session = False
    use_shell = False
    wait_for_process = not detached and not non_blocking

    stdout = None
    stderr = None

    if get_output or use_custom_pipe:
        if detached or non_blocking:
            raise ValueError("get_output can only be used when detached=False and non_blocking=False")
        stdout = subprocess.PIPE
        stderr = subprocess.PIPE
    elif detached and output_file:
        stdout = open(output_file, "a")
        stderr = subprocess.STDOUT
    elif detached:
        stdout = open(os.devnull, "w")
        stderr = subprocess.STDOUT

    if IS_WIN32:
        if detached:
            creationflags |= subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
        if new_console:
            creationflags |= subprocess.CREATE_NEW_CONSOLE
        else:
            executable = Path(command[0])
            if executable.stem == 'python':
                if executable.with_name('pythonw.exe').exists():
                    command[0] = str(executable.with_name('pythonw.exe'))
            creationflags |= subprocess.CREATE_NO_WINDOW # TODO make optional
        stdin = subprocess.DEVNULL if detached else None
    else:
        if detached:
            start_new_session = True
            stdin = open(os.devnull, "r")
        if new_console:
            terminal = os.environ.get("TERMINAL", "x-terminal-emulator")
            if terminal in ["gnome-terminal", "konsole", "xfce4-terminal"]:
                command = [terminal, "--", *command]
            else:
                command = f'{terminal} -e "{subprocess.list2cmdline(command)}"'
                use_shell = True

    after_start_callback: Callable|None = None
    _read_pipe = _write_pipe = None
    if use_custom_pipe:
        extra_envs, after_start_callback, popen_kw, _read_pipe, _write_pipe = custom_pipe.create_pipe()
        if extra_envs:
            new_env.update(extra_envs)
        if popen_kw:
            kwargs.update(popen_kw)

    logger.debug('CMD: %s', ' '.join(command) if isinstance(command, list) else command)
    if os.name == 'nt':
        kwargs.update(dict(
            encoding="utf-8",
            errors="replace",
            )
        )
    process_timeout = kwargs.pop('timeout', None)
    process = subprocess.Popen(
        command,
        env=new_env,
        stdout=stdout,
        stderr=stderr,
        stdin=stdin,
        start_new_session=start_new_session,
        creationflags=creationflags,
        shell=use_shell,
        cwd=workdir,
        **kwargs
    )
    if after_start_callback:
        after_start_callback()

    if detached and output_file and not get_output:
        stdout.close()

    if wait_for_process:
        try:
            if get_output:
                output, error = process.communicate(timeout=process_timeout)
                logging.debug(f'Exit Code: {process.returncode}')
                if process.returncode != 0:
                    if isinstance(error, bytes):
                        error = error.decode()
                    print(error, file=sys.stderr)
                if isinstance(output, bytes):
                    output = output.decode()
                return output
            elif use_custom_pipe:
                output, error = process.communicate(timeout=process_timeout)
                if error:
                    if isinstance(error, bytes):
                        error = error.decode()
                    msg = error.strip().split('\n')[-1]
                    print(error, file=sys.stderr, flush=True)
                    raise RuntimeError(msg)
                if isinstance(_read_pipe, int):
                    num = _read_pipe
                else:
                    num = _read_pipe.value
                return custom_pipe.read_pipe(num)
            else:
                process.wait()
                logging.debug(f'Exit Code: {process.returncode}')

                if exit_on_done:
                    sys.exit(process.returncode)
                return process.returncode

        except KeyboardInterrupt:
            terminate_child(process)
            if exit_on_done:
                sys.exit(1)

    elif non_blocking or detached:
        return process

    return None


def write_to_pipe(data: str|bytes):
    """
    Use open_pipe=True with function start_process to create custom pipe and write to him in child process
    """
    return custom_pipe.write_pipe(data)


def pipe_is_allowed():
    return custom_pipe.pipe_defined()


def process_exists(pid) -> bool:
    """
    Process is running
    """
    try:
        os.kill(pid, 0)
    except (ProcessLookupError, OSError, SystemError):
        return False
    except PermissionError:
        return True
    else:
        return True


def restart_with_env(env: dict):
    """Restart current process with extend envs"""
    env = {**os.environ.copy(), **env}
    start_process(sys.argv, env=env, replace=True, workdir=os.getcwd())


def is_started_as_admin() -> bool:
    if IS_WIN32:
        import ctypes
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    else:
        return os.geteuid() == 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Start a process with different execution modes")


    class ParseEnvVariables(argparse.Action):
        def __call__(self, parser, namespace, values, option_string=None):
            env_vars = getattr(namespace, self.dest, None)
            if env_vars is None:
                env_vars = {}
            if '=' not in values:
                raise argparse.ArgumentError(self,
                                             f"Invalid environment variable format: {values}. Expected KEY=VALUE.")
            key, val = values.split('=', 1)
            env_vars[key] = val

            setattr(namespace, self.dest, env_vars)

    parser.add_argument("-d", "--detached", action="store_true", help="Run the process in the background")
    parser.add_argument("-n", "--new-console", action="store_true", help="Run the process in a new terminal window")
    parser.add_argument("-r", "--replace", action="store_true", help="replace current process. Other flags will be ignores")
    parser.add_argument("-b", "--non-blocking", action="store_true",
                        help="Run the process as a child without blocking the parent")
    parser.add_argument("-e", "--env", action=ParseEnvVariables, help="Environment variables (KEY=VALUE).",
                        metavar="KEY=VALUE")
    parser.add_argument("-o", "--output-file", help="File to redirect output of a detached process")
    parser.add_argument("-w", "--workdir", help="Working directory for the command")
    parser.add_argument("-g", "--get-output", action="store_true",
                        help="Get output from the process (only when not detached and not non-blocking)")
    parser.add_argument("-x", "--exit-on-done", help="Exit when subprocess exited", action="store_true", default=True)
    parser.add_argument("command", nargs=argparse.REMAINDER, help="Command to execute")

    args = parser.parse_args()

    if not args.command:
        parser.error("No command provided for execution")

    result = start_process(
        args.command,
        env=args.env,
        detached=args.detached,
        new_console=args.new_console,
        non_blocking=args.non_blocking,
        output_file=args.output_file,
        replace=args.replace,
        workdir=args.workdir,
        get_output=args.get_output
    )
    if args.get_output:
        print(result)