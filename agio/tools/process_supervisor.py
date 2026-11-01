"""
Console process supervisor.

Runs a command and waits for its WHOLE descendant tree to finish, not just for
the direct child. Required for applications that detach their real process:
for example houdini's initial process forks the UI, calls setsid() and exits
a few seconds after the start. A plain console wrapper (bash/cmd) exits
together with the leader and closes the console too early.

The supervisor is marked as a child subreaper (PR_SET_CHILD_SUBREAPER),
so any orphaned descendant of the started process is re-parented to the
supervisor and can be waited on. The console closes only when the last
process of the application tree exits.

Exit code: the leader's exit code, or the first non-zero exit code of any
descendant if the leader succeeded.
"""
import ctypes
import os
import sys

PR_SET_CHILD_SUBREAPER = 36


def _set_subreaper():
    libc = ctypes.CDLL(None, use_errno=True)
    if libc.prctl(PR_SET_CHILD_SUBREAPER, 1, 0, 0, 0) != 0:
        raise OSError(ctypes.get_errno(), 'prctl(PR_SET_CHILD_SUBREAPER) failed')


def main() -> int:
    argv = sys.argv[1:]
    hold = '--hold' in argv
    command = argv[argv.index('--') + 1:] if '--' in argv else []
    if not command:
        print('No command provided for supervision', file=sys.stderr)
        return 1

    # terminal signals are delivered to the whole foreground group,
    # the command must handle them itself
    import signal
    signal.signal(signal.SIGINT, signal.SIG_IGN)

    _set_subreaper()
    leader = os.fork()
    if leader == 0:
        try:
            os.execvpe(command[0], command, os.environ)
        except FileNotFoundError:
            print(f'Error: {command[0]} not found.', file=sys.stderr)
            os._exit(1)

    leader_status = None
    failed_child = None
    while True:
        try:
            pid, status = os.wait()
        except ChildProcessError:
            break   # no children left: the whole tree is finished
        if pid == leader:
            leader_status = status
        elif os.waitstatus_to_exitcode(status) != 0 and failed_child is None:
            failed_child = status

    rc = os.waitstatus_to_exitcode(leader_status) if leader_status is not None else 0
    if not rc and failed_child is not None:
        rc = os.waitstatus_to_exitcode(failed_child)
    if hold and rc != 0:
        print()
        try:
            input('Press Enter to close...')
        except (EOFError, KeyboardInterrupt):
            pass
    return rc


if __name__ == '__main__':
    sys.exit(main())
