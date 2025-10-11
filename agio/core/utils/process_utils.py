import logging
import os
import shlex
import sys
import signal
import subprocess
import argparse
from contextlib import contextmanager
from typing import Iterable

logger = logging.getLogger(__name__)

def terminate_child(proc):
    if sys.platform == "win32":
        subprocess.call(["taskkill", "/F", "/T", "/PID", str(proc.pid)])
    else:
        os.killpg(os.getpgid(proc.pid), signal.SIGKILL)


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
        open_pipe: bool = False,
        pipe_open_mode='text',  # text|binary
        exit_on_done=False,
        **kwargs
):
    """
    Universal function to start a process with different modes.

    Automatically terminates child process if parent is killed (when not detached).
    Propagates exit code from child to parent if the child crashes.
    """
    if get_output and open_pipe:
        raise Exception("open_pipe and get_output are mutually exclusive")
    if detached and open_pipe:
        raise Exception('Argument open_pipe cannot be used with detached=True')
    if open_pipe and replace:
        raise Exception('Argument open_pipe cannot be used with replace=True')
    if detached and replace:
        raise Exception('Argument replace cannot be used with detached=True')
    if replace and get_output:
        raise Exception('Argument replace cannot be used with get_output=True')
    if open_pipe:
        if pipe_open_mode == "text":
            pipe_mode = 'r'
        elif pipe_open_mode == "binary":
            pipe_mode = 'rb'
        else:
            raise ValueError("pipe_open_mode must be 'text' or 'binary'")

    new_env = os.environ.copy()
    if clear_env:
        for env_name in clear_env:
            new_env.pop(env_name, None)
    if env:
        new_env.update(env)
    if workdir:
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

    if get_output:
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

    if sys.platform == "win32":
        if detached:
            creationflags |= subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
        if new_console:
            creationflags |= subprocess.CREATE_NEW_CONSOLE
        else:
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

    close_fds = True if sys.platform != "win32" else False,

    write_fd = read_fd = None
    if open_pipe:
        read_fd, write_fd = os.pipe()
        os.set_inheritable(write_fd, True)
        close_fds = False
        new_env['AGIO_CUSTOM_PIPE_FILE_NO'] = str(write_fd)
        new_env['AGIO_CUSTOM_PIPE_FILE_MODE'] = pipe_open_mode
    logger.debug('CMD: %s', ' '.join(command) if isinstance(command, list) else command)
    process = subprocess.Popen(
        command,
        env=new_env,
        stdout=stdout,
        stderr=stderr,
        stdin=stdin,
        close_fds=close_fds,
        start_new_session=start_new_session,
        creationflags=creationflags,
        shell=use_shell,
        cwd=workdir,
        **kwargs
    )
    if write_fd:
        os.close(write_fd)

    if detached and output_file and not get_output:
        stdout.close()

    if not detached:
        if sys.platform == "win32":
            pass # TODO close child process on parent exited
            # job = ctypes.windll.kernel32.CreateJobObjectW(None, None)
            # info = ctypes.wintypes.JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
            # info.BasicLimitInformation.LimitFlags = 0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
            # ctypes.windll.kernel32.SetInformationJobObject(job, 9, ctypes.byref(info), ctypes.sizeof(info))
            # ctypes.windll.kernel32.AssignProcessToJobObject(job, process._handle)
        else:
            pass # TODO error if called from non main thread
            # def handle_parent_exit(*_):
            #     terminate_child(process)
            #     sys.exit(1)
            # signal.signal(signal.SIGTERM, handle_parent_exit)
            # signal.signal(signal.SIGINT, handle_parent_exit)

    if wait_for_process:
        try:
            if get_output:
                output, error = process.communicate()
                logging.debug(f'Exit Code: {process.returncode}')
                if process.returncode != 0:
                    if isinstance(error, bytes):
                        error = error.decode()
                    print(error, file=sys.stderr)
                if isinstance(output, bytes):
                    output = output.decode()
                return output
            elif open_pipe:
                if not read_fd:
                    raise Exception("open_pipe requires read_fd object")
                with os.fdopen(read_fd, pipe_mode) as data_pipe_handler:
                    data = data_pipe_handler.read()
                return data
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
        # Return the Popen object if non-blocking or detached.
        return process
    return None


def write_to_pipe(data: str):
    """
    Use open_pipe=True with function start_process to create custom pipe and write to him in child process
    """
    if not pipe_is_allowed():
        raise Exception("Data Pipe is not allowed")
    mode = os.getenv('AGIO_CUSTOM_PIPE_FILE_MODE')
    if not mode:
        if isinstance(data, bytes):
            mode = 'wb'
        elif isinstance(data, str):
            mode = 'w'
        else:
            raise TypeError('data must be str or bytes')
    pipe_num = os.getenv('AGIO_CUSTOM_PIPE_FILE_NO')
    if not pipe_num:
        raise ValueError('Custom pipe file not set')
    with os.fdopen(int(pipe_num), mode) as data_pipe_handler:
        data_pipe_handler.write(data)
        data_pipe_handler.flush()


@contextmanager
def data_pipe():
    """
    Use open_pipe=True with function start_process to create custom pipe and write to him in child process
    Context manager allow you to write multiple times.
    Use write_to_pipe(data) to write and close in single step/

    Usage:
    >>> with data_pipe() as pipe:
    >>>     ...
    >>>     pipe.write('text1')
    >>>     ...
    >>>     pipe.write('text2')
    """
    pipe_num = os.getenv('AGIO_CUSTOM_PIPE_FILE_NO')
    if not pipe_num:
        raise ValueError('Custom pipe file not set')
    mode = os.getenv('AGIO_CUSTOM_PIPE_FILE_MODE')
    with os.fdopen(int(pipe_num), mode) as data_pipe_handler:
        yield data_pipe_handler
        data_pipe_handler.flush()


def pipe_is_allowed():
    return bool(os.getenv('AGIO_CUSTOM_PIPE_FILE_NO'))


def process_exists(pid) -> bool:
    """
    Process is running
    """
    try:
        os.kill(pid, 0)
    except (ProcessLookupError, OSError):
        return False
    except PermissionError:
        return True
    else:
        return True


def restart_with_env(env: dict):
    """Restart current process with extend envs"""
    cmd = [sys.executable]+sys.argv
    env = {**os.environ.copy(), **env}
    start_process(cmd, env=env, replace=True, workdir=os.getcwd())


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