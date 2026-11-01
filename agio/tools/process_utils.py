import logging
import os
import shlex
import shutil
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


def _wait_process_tree(process: "subprocess.Popen", poll_interval: float = 0.5) -> int:
    """
    Windows substitute for the posix subreaper wait:
    blocks until the started process AND all its descendants terminate.

    Gui launchers often exit right after the real application is started
    (the calc stub, dcc apps spawning a detached ui process), so waiting
    for the direct child is not enough. Descendants are adopted by parent
    pid: on Windows a process keeps the pid of its (even already dead)
    parent, so the tree stays discoverable after the launcher exits.
    Returns the exit code of the direct child.
    """
    import psutil
    import time

    # dead pids stay in the set: a gui app activated by an already exited
    # launcher keeps the launcher pid as its parent pid, so the parent must
    # remain in the set for one more poll to adopt the app process
    watched = {process.pid}
    try:
        while True:
            adopted = set()
            for proc in psutil.process_iter(['pid', 'ppid']):
                try:
                    pid, ppid = proc.info['pid'], proc.info['ppid']
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
                if ppid in watched and pid not in watched:
                    adopted.add(pid)
            watched |= adopted
            if not any(psutil.pid_exists(pid) for pid in watched):
                break
            time.sleep(poll_interval)
    except KeyboardInterrupt:
        terminate_child(process)
        return 1
    process.poll()
    return process.returncode if process.returncode is not None else 0



def start_process(
        command: list[str] | tuple[str] | str,
        env: dict = None,
        clear_env: list = None,
        detached: bool = False,
        replace: bool = False,
        new_console: bool = False,
        keep_console: bool = False,
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
        # command = [shlex.quote(x).replace("'", '"') for x in command]  # TODO fix quotes for Windows os ?
        if sys.platform == 'win32':
            target_executable = executable
            if not os.path.isabs(target_executable):
                found_path = shutil.which(target_executable)
                if found_path:
                    target_executable = found_path
            try:
                process = subprocess.Popen(command, env=new_env)
                sys.exit(_wait_process_tree(process))
            except FileNotFoundError:
                print(f"Error: {target_executable} not found.")
                sys.exit(1)
        else:
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
    elif new_console and (detached or non_blocking):
        if IS_WIN32:
            # the new console owns stdio: a child started with
            # CREATE_NEW_CONSOLE writes to the console only when its
            # std handles are not redirected
            stdout = None
            stderr = None
        else:
            # the terminal emulator process owns the output;
            # do not keep the parent's stdout/stderr open, otherwise
            # a caller reading pipes will wait until the console is closed
            stdout = open(os.devnull, "w")
            stderr = subprocess.STDOUT
    elif detached:
        stdout = open(os.devnull, "w")
        stderr = subprocess.STDOUT

    if IS_WIN32:
        # DETACHED_PROCESS cannot be combined with CREATE_NEW_CONSOLE
        if detached and not new_console:
            creationflags |= subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
        if new_console:
            if keep_console:
                if isinstance(command, str):
                    command = shlex.split(command)
                if command and command[0].lower() not in ('cmd', 'cmd.exe'):
                    # the launched chain waits for the whole process tree of
                    # the app, so the console closes with the app; on error
                    # (non-zero exit code) "pause" keeps the console open
                    command_line = subprocess.list2cmdline(list(command))
                    command = f'cmd /c ({command_line}) || pause'
            creationflags |= subprocess.CREATE_NEW_CONSOLE
        else:
            if isinstance(command, (list, tuple)) and command:
                executable = Path(command[0])
                if executable.stem == 'python':
                    if executable.with_name('pythonw.exe').exists():
                        command[0] = str(executable.with_name('pythonw.exe'))
            creationflags |= subprocess.CREATE_NO_WINDOW # TODO make optional
        # with a new console the child must read the console stdin,
        # DEVNULL would close "cmd /c ..." right after the command exits
        stdin = subprocess.DEVNULL if detached and not new_console else None
    else:
        if detached:
            start_new_session = True
            stdin = open(os.devnull, "r")
        elif not get_output and not use_custom_pipe:
            stdin = open(os.devnull, "r")
        if new_console:
            if isinstance(command, str):
                command_list = shlex.split(command)
            else:
                command_list = list(command)
            terminal = os.environ.get("TERMINAL", "x-terminal-emulator")
            # resolve wrappers like x-terminal-emulator to the real terminal
            terminal = os.path.realpath(shutil.which(terminal) or terminal)
            terminal_name = Path(terminal).stem
            # wrap the command into the process tree supervisor:
            # the console must live while ANY process of the application is running
            # (dcc apps like houdini fork the ui process, detach it with setsid and exit)
            # -P keeps the script dir off sys.path, otherwise agio/tools/enum.py
            # shadows the stdlib enum module and the supervisor crashes on import
            supervisor = [sys.executable or "python3", "-P",
                          str(Path(__file__).with_name("process_supervisor.py"))]
            if keep_console:
                command = [*supervisor, "--hold", "--", *command_list]
            else:
                command = [*supervisor, "--", *command_list]
            # konsole ignores args after "--" and starts an interactive shell,
            # so "-e" is the only reliable separator for it
            sep = "--" if terminal_name in ("gnome-terminal", "xfce4-terminal") else "-e"
            command = [terminal, sep, *command]

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
    validate_envs(new_env)
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
                sys.stdout.flush()
                sys.stderr.flush()
                if not IS_WIN32:
                    try:
                        import termios
                        _saved_tty_attrs = termios.tcgetattr(sys.stdin.fileno())
                    except (termios.error, AttributeError, OSError):
                        _saved_tty_attrs = None
                else:
                    _saved_tty_attrs = None
                
                process.wait()
                if not IS_WIN32 and _saved_tty_attrs is not None:
                    try:
                        import termios
                        termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, _saved_tty_attrs)
                    except (termios.error, AttributeError, OSError):
                        pass
                
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


def validate_envs(envs: dict, covert_to_str: bool = False):
    for k, v in envs.items():
        if not isinstance(v, str):
            if covert_to_str:
                envs[k] = str(v)
            else:
                raise ValueError(f'Key {k} is not a string: type {type(v)} [{v!r}]')


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