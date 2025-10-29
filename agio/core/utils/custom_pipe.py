import io
import os
import sys
from contextlib import contextmanager

IS_WINDOWS = sys.platform == 'win32'
FILE_NO_ENV = 'AGIO_CUSTOM_PIPE_FILE_NO'

# create

def create_pipe() -> (str, callable, dict, dict):
    """
    Create custom pipe
    return
    str - file handler num for env
    callable - callable function for call after subprocess started
    dict - kwargs for subprocess call
    """
    if IS_WINDOWS:
        return create_pipe_windows()
    else:
        return create_pipe_posix()


def create_pipe_windows():
    from ctypes import windll, byref, c_void_p, Structure, c_int
    kernel = windll.kernel32

    class SECURITY_ATTRIBUTES(Structure):
        _fields_ = [
            ("nLength", c_int),
            ("lpSecurityDescriptor", c_void_p),
            ("bInheritHandle", c_int),
        ]


    read_h = c_void_p()
    write_h = c_void_p()

    sa = SECURITY_ATTRIBUTES()
    sa.nLength = 12
    sa.lpSecurityDescriptor = None
    sa.bInheritHandle = 1

    if not kernel.CreatePipe(byref(read_h), byref(write_h), byref(sa), 0):
        raise OSError("CreatePipe failed")

    handle_flag_inherit = 1
    kernel.SetHandleInformation(write_h, handle_flag_inherit, handle_flag_inherit)

    return ({FILE_NO_ENV: str(write_h.value)},      # env
            lambda : kernel.CloseHandle(write_h),   # callback
            {'close_fds': False},                                     # subprocess.Popen kwargs
            read_h, write_h
            )


def create_pipe_posix():
    read_fd, write_fd = os.pipe()
    os.set_inheritable(write_fd, True)
    return (
        {FILE_NO_ENV: str(write_fd)},   # env
        lambda : os.close(write_fd),    # callback
        {'close_fds': False},           # subprocess.Popen kwargs
        read_fd, write_fd
    )


# write

def write_pipe(data):
    if not isinstance(data, bytes):
        raise TypeError("data must be bytes or str")
    if IS_WINDOWS:
        return write_pipe_windows(data)
    else:
        return write_pipe_posix(data)


def write_pipe_windows(data: bytes):
    pipe_handler_num = get_pipe_num()
    fd = try_open_os_fhandle(int(pipe_handler_num), os.O_WRONLY)
    with os.fdopen(fd, 'wb', buffering=0) as pipe:
        pipe.write(data)
        pipe.flush()


def try_open_os_fhandle(handle_num, mode):
    import msvcrt
    from ctypes import FormatError, get_last_error
    try:
        fd = msvcrt.open_osfhandle(int(handle_num), mode)
        return fd
    except OSError as e:
        err_code = get_last_error()
        err_text = FormatError(err_code).strip()
        raise OSError(f"{str(e).split(':', 1)[-1]}. code={err_code}, message={err_text}")


def write_pipe_posix(data):
    pipe_handler_num = get_pipe_num()
    with os.fdopen(pipe_handler_num, 'wb', buffering=0) as data_pipe_handler:
        data_pipe_handler.write(data)
        data_pipe_handler.flush()


@contextmanager
def data_pipe():
    """
    Use open_pipe=True with function start_process to create custom pipe and write to him in child process
    Context manager allow you to write multiple times.
    Use write_to_pipe(data) to write and close in single step

    Usage:
    >>> with data_pipe() as pipe:
    >>>     ...
    >>>     pipe.write('text1')
    >>>     ...
    >>>     pipe.write('text2')
    """
    pipe_handler_num = get_pipe_num()
    if IS_WINDOWS:
        import msvcrt

        fd = msvcrt.open_osfhandle(pipe_handler_num, os.O_WRONLY)
        with os.fdopen(fd, 'wb', buffering=0) as pipe:
            yield pipe
            pipe.flush()
    else:
        with os.fdopen(pipe_handler_num, 'wb') as data_pipe_handler:
            yield data_pipe_handler
            data_pipe_handler.flush()


# read

def read_pipe(pipe_num: int):
    if IS_WINDOWS:
        return read_pipe_windows(pipe_num)
    else:
        return read_pipe_posix(pipe_num)

def read_pipe_windows(pipe_handler_num):
    fd_read = try_open_os_fhandle(pipe_handler_num, os.O_RDONLY)
    result = io.BytesIO()
    with os.fdopen(fd_read, "rb", buffering=0) as pipe:
        for chunk in iter(lambda: pipe.read(1024), b""):
            result.write(chunk)
    return result.getvalue()


def read_pipe_posix(pipe_handler_num: int):
    with os.fdopen(pipe_handler_num, 'rb') as data_pipe_handler:
        data = data_pipe_handler.read()
    return data

# other

def pipe_defined():
    return bool(os.getenv(FILE_NO_ENV))


def get_pipe_num():
    num = os.getenv(FILE_NO_ENV)
    if not num:
        raise OSError("Pipe num not defined")
    return int(num)

