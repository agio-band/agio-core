import logging
import os
import shlex
import sys
import signal
import subprocess
import argparse
from contextlib import contextmanager
from pathlib import Path
from typing import Iterable

logger = logging.getLogger(__name__)

def terminate_child(proc):
    """
    Terminates a process and its whole process group (or job).
    """
    if sys.platform == "win32":
        # /F: Force termination
        # /T: Terminate the specified process and any child processes started by it
        subprocess.call(["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        # Send SIGKILL to the entire process group
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
        open_pipe: bool = False,
        pipe_open_mode='text',  # text|binary
        exit_on_done=False,
        **kwargs
):
    """
    Universal function to start a process with different modes.

    Returns:
        str/bytes: If get_output or open_pipe is True.
        int: If blocking (wait_for_process=True) and not returning output (return code).
        subprocess.Popen: If non_blocking or detached is True.
        None: Otherwise (e.g., if exit_on_done is True).
    """

    # --- Input Validation ---
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

    # --- Environment and Working Directory Setup ---
    new_env = os.environ.copy()
    if clear_env:
        for env_name in clear_env:
            new_env.pop(env_name, None)
    if env:
        new_env.update(env)

    if workdir:
        workdir = os.path.abspath(os.path.expanduser(workdir))
        if not os.path.isdir(workdir):
            print(f"Error: Working directory '{workdir}' does not exist.", file=sys.stderr)
            sys.exit(1)

    if isinstance(command, Iterable) and not isinstance(command, str):
        command = list(map(str, command))

    # --- Replace Mode (os.execve/os.execvpe) ---
    if replace:
        if isinstance(command, str):
            command = shlex.split(command)
        executable = command[0]
        if workdir:
            try:
                os.chdir(workdir)
            except OSError as e:
                print(f"Error changing directory: {e}", file=sys.stderr)
                sys.exit(1)

        # os.execvpe searches PATH; os.execve requires an absolute path.
        if os.path.isabs(executable):
            os.execve(executable, command, new_env)
        else:
            os.execvpe(executable, command, new_env)

    # --- Popen Initialization ---
    creationflags = 0
    stdin = None
    stdout = None
    stderr = None
    start_new_session = False
    use_shell = False

    # Corrected: wait_for_process means blocking
    wait_for_process = not detached and not non_blocking

    # --- I/O Redirection Logic ---
    if get_output:
        # Output must be piped back to parent for capture
        if detached or non_blocking:
            raise ValueError("get_output can only be used when detached=False and non_blocking=False")
        stdout = subprocess.PIPE
        stderr = subprocess.PIPE

    elif detached and output_file:
        # Redirect output to a file when detached. File handle must be closed manually later.
        try:
            # We open stdout to a file and redirect stderr to the same place.
            stdout = open(output_file, "a")
            stderr = subprocess.STDOUT
        except Exception as e:
            logging.error(f"Failed to open output file {output_file}: {e}")
            raise

    elif detached:
        # Use DEVNULL constant to discard output and prevent resource leaks.
        stdout = subprocess.DEVNULL
        stderr = subprocess.DEVNULL

    # --- Platform-Specific Flags and Configuration ---
    if sys.platform == "win32":
        if detached:
            # DETACHED_PROCESS: Ensures process is fully independent.
            # CREATE_NEW_PROCESS_GROUP: Prevents signals from reaching the detached group.
            creationflags |= subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP

        if new_console:
            # CREATE_NEW_CONSOLE: Guarantees a new console window if one is not created implicitly.
            creationflags |= subprocess.CREATE_NEW_CONSOLE
        else:
            # If new_console=False, attempt to hide the console.
            executable = Path(command[0])

            # Optimization: Use pythonw.exe for python scripts to avoid console flash
            if executable.stem == 'python':
                if executable.with_name('pythonw.exe').exists():
                    command[0] = str(executable.with_name('pythonw.exe'))
            else:
                # CREATE_NO_WINDOW: Explicitly prevents the creation of a console window.
                # This overrides the implicit new console creation from DETACHED_PROCESS for console apps.
                creationflags |= subprocess.CREATE_NO_WINDOW

        # DEVNULL constant for stdin when detached is clean and correct for Windows.
        stdin = subprocess.DEVNULL if detached else None

    else:  # Unix-like systems
        if detached:
            # Setsid/Start_new_session: Creates a new process group for detaching.
            start_new_session = True
            # When detached, stdin must be explicitly opened from /dev/null for reading
            # (or using the DEVNULL constant) to prevent blocking if the child reads from stdin.
            stdin = open(os.devnull, "r")

        if new_console:
            # Launching a terminal emulator on Unix for new_console functionality
            terminal = os.environ.get("TERMINAL", "x-terminal-emulator")
            if terminal in ["gnome-terminal", "konsole", "xfce4-terminal"]:
                command = [terminal, "--", *command]
            else:
                # Fallback, requires shell=True
                command = f'{terminal} -e "{subprocess.list2cmdline(command)}"'
                use_shell = True

    # Corrected: close_fds should be a boolean. True is standard for Unix unless pipes are needed.
    close_fds = True if sys.platform != "win32" else False

    write_fd = read_fd = None
    if open_pipe:
        # Prepare the pipe for inter-process communication
        read_fd, write_fd = os.pipe()
        os.set_inheritable(write_fd, True)
        close_fds = False  # Must be False to allow the child to inherit the pipe FD
        new_env['AGIO_CUSTOM_PIPE_FILE_NO'] = str(write_fd)
        new_env['AGIO_CUSTOM_PIPE_FILE_MODE'] = pipe_open_mode

    # --- Launch Process ---
    logging.debug('CMD: %s', ' '.join(command) if isinstance(command, list) else command)
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

    # --- Resource Cleanup (Post-Popen) ---
    if write_fd:
        # Close the write end of the pipe in the parent immediately
        os.close(write_fd)

    # 1. Close the file handle used for stdout/stderr redirection when detached
    if detached and output_file and stdout is not None and hasattr(stdout, 'close'):
        try:
            stdout.close()
        except:
            pass  # Ignore if close fails

    # 2. Close stdin handle opened from os.devnull on Unix/Linux when detached
    if sys.platform != "win32" and detached and stdin is not None and hasattr(stdin, 'close'):
        try:
            stdin.close()
        except:
            pass  # Ignore if close fails

    # --- Parent Exit Handling (Kill Child) ---
    if not detached and not replace:
        if sys.platform == "win32":
            import ctypes
            # TODO: Close child process on parent exited -> Use Job Object
            if "job" not in kwargs:
                try:
                    # Create Job Object with JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE (0x2000)
                    job = ctypes.windll.kernel32.CreateJobObjectW(None, None)
                    info = ctypes.wintypes.JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
                    info.BasicLimitInformation.LimitFlags = 0x2000
                    ctypes.windll.kernel32.SetInformationJobObject(job, 9, ctypes.byref(info), ctypes.sizeof(info))

                    # Assign the new process to the job
                    handle = ctypes.windll.kernel32.OpenProcess(0x1F0FFF, False, process.pid)  # PROCESS_ALL_ACCESS
                    ctypes.windll.kernel32.AssignProcessToJobObject(job, handle)
                    ctypes.windll.kernel32.CloseHandle(handle)

                    # Store the job object handle so it isn't garbage collected immediately
                    process.job_object = job
                except Exception as e:
                    logging.warning(f"Could not assign process to Job Object (kill on parent exit): {e}")

        else:
            # TODO: Signal handlers (SIGTERM/SIGINT) for Unix should be handled by the main application
            # (or by using prctl/setsid in combination with start_new_session logic).
            # The current approach relies on the process remaining in the session/group,
            # which is the default non-detached behavior.
            pass

    # --- Blocking / Non-Blocking Execution ---
    if wait_for_process:
        try:
            if get_output:
                # Blocking call to read all output
                output, error = process.communicate()
                logging.debug(f'Exit Code: {process.returncode}')

                if process.returncode != 0:
                    error_str = error.decode(errors='replace') if isinstance(error, bytes) else error
                    print(error_str, file=sys.stderr)

                output_str = output.decode(errors='replace') if isinstance(output, bytes) else output
                return output_str

            elif open_pipe:
                # Read from the pipe created earlier
                if not read_fd:
                    raise Exception("open_pipe requires read_fd object")

                # The pipe handler ensures the read end is closed upon exit
                with os.fdopen(read_fd, pipe_mode) as data_pipe_handler:
                    data = data_pipe_handler.read()

                # Wait for the child process to complete after reading the pipe data
                process.wait()
                return data

            else:
                # Simple blocking wait for return code
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
        # Return the Popen object for the caller to manage
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
    except (ProcessLookupError, OSError, SystemError):
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