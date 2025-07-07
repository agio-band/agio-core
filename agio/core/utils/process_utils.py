import logging
import os
import shlex
import sys
import signal
import subprocess
import argparse
import ctypes
from typing import Iterable


def terminate_child(proc):
    if sys.platform == "win32":
        subprocess.call(["taskkill", "/F", "/T", "/PID", str(proc.pid)])
    else:
        os.killpg(os.getpgid(proc.pid), signal.SIGKILL)


def start_process(
        command: list[str] | tuple[str] | str,
        envs: dict = None,
        detached: bool = False,
        replace: bool = False,
        new_console: bool = False,
        non_blocking: bool = False,
        output_file=None,
        workdir: str = None,
        get_output: bool = False,
        **kwargs
):
    """
    Universal function to start a process with different modes.

    Automatically terminates child process if parent is killed (when not detached).
    Propagates exit code from child to parent if the child crashes.
    """
    new_env = os.environ.copy()
    if envs:
        new_env.update(envs)

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

    process = subprocess.Popen(
        command,
        env=new_env,
        stdout=stdout,
        stderr=stderr,
        stdin=stdin,
        close_fds=True if sys.platform != "win32" else False,
        start_new_session=start_new_session,
        creationflags=creationflags,
        shell=use_shell,
        cwd=workdir,
        **kwargs
    )

    if detached and output_file and not get_output:
        stdout.close()

    if not detached:
        if sys.platform == "win32":
            job = ctypes.windll.kernel32.CreateJobObjectW(None, None)
            info = ctypes.wintypes.JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
            info.BasicLimitInformation.LimitFlags = 0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
            ctypes.windll.kernel32.SetInformationJobObject(job, 9, ctypes.byref(info), ctypes.sizeof(info))
            ctypes.windll.kernel32.AssignProcessToJobObject(job, process._handle)
        else:
            def handle_parent_exit(*_):
                terminate_child(process)
                sys.exit(1)
            signal.signal(signal.SIGTERM, handle_parent_exit)
            signal.signal(signal.SIGINT, handle_parent_exit)

    if wait_for_process:
        try:
            if get_output:
                output, error = process.communicate()
                logging.debug(f'Exit Code: {process.returncode}')
                if process.returncode != 0:
                  print(error.decode(), file=sys.stderr)
                return output.decode()
            else:
                process.wait()
                logging.debug(f'Exit Code: {process.returncode}')
                sys.exit(process.returncode)

        except KeyboardInterrupt:
            terminate_child(process)
            sys.exit(1)
    elif non_blocking or detached:
        # Return the Popen object if non-blocking or detached.
        return process
    return None


def process_exists(pid):
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    else:
        return True


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
    parser.add_argument("command", nargs=argparse.REMAINDER, help="Command to execute")

    args = parser.parse_args()

    if not args.command:
        parser.error("No command provided for execution")

    result = start_process(
        args.command,
        envs=args.env,
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