import atexit
import logging
import os
import signal
import sys
import threading
import asyncio

from agio.tools import setup_logger, env_names  # noqa: F401
from agio.core.events import emit as _emit, subscribe as _subscribe
from agio.core.init.init_packages import init_packages
from agio.core.init.init_plugins import init_plugins
from agio.tools import process_hub

# add extra paths before initialize packages
extra_packages_env = os.getenv(env_names.EXTRA_PACKAGES)
if extra_packages_env:
    for _pth in extra_packages_env.split(os.pathsep):
        sys.path.append(_pth)


logger = logging.getLogger(__name__)

init_packages()
init_plugins()
_process_hub = process_hub.ProcessHub()
_subscribe('core.app.exit', _process_hub.shutdown)
_emit('core.app.logger_created', {'logger': logger})


def _before_exit_event(signum, frame):
    print()
    logger.debug('Receive exit signal')
    _emit('core.app.exit')
    # signal.signal(signum, signal.SIG_DFL)
    # signal.raise_signal(signum)

# if threading.current_thread() is threading.main_thread():
#     signal.signal(signal.SIGINT, _before_exit_event)
#     signal.signal(signal.SIGTERM, _before_exit_event)
# else:
#     atexit.register(_before_exit_event)


# wraps for Ctrl+C exceptions for custom agio event core.app.exit
original_handler = signal.getsignal(signal.SIGINT)
try:
    # exit event for async apps
    loop = asyncio.get_running_loop()
    def callback_for_async():
        _before_exit_event(signal.SIGINT, None)
        if callable(original_handler):
            if original_handler not in (signal.SIG_IGN, signal.SIG_DFL):
                original_handler(signal.SIGINT, None)
    loop.add_signal_handler(signal.SIGINT, callback_for_async)
except RuntimeError:
    # exit event for sync apps and qt apps
    if threading.current_thread() is threading.main_thread():
        def sync_wrapper(signum, frame):
            _before_exit_event(signum, frame)
            if callable(original_handler):
                try:
                    original_handler(signum, frame)
                except (KeyboardInterrupt, SystemExit):
                    pass
                os._exit(0)
        signal.signal(signal.SIGINT, sync_wrapper)
        signal.signal(signal.SIGTERM, sync_wrapper)
    else:
        atexit.register(lambda: _before_exit_event(None, None))



# original_handler = signal.getsignal(signal.SIGINT)
#
# def smart_exit(sig=signal.SIGINT, frame=None):
#     _before_exit_event(sig, frame)
#     # Пытаемся вызвать оригинал, если это функция
#     if callable(original_handler) and original_handler not in (signal.SIG_IGN, signal.SIG_DFL):
#         try:
#             original_handler(sig, frame)
#         except (KeyboardInterrupt, SystemExit):
#             pass
#     # Если мы в главном потоке синхронного кода или Qt — рубим процесс
#     if threading.current_thread() is threading.main_thread():
#         os._exit(0)
#
# try:
#     # Асинхронный контекст
#     loop = asyncio.get_running_loop()
#     loop.add_signal_handler(signal.SIGINT, smart_exit)
# except RuntimeError:
#     # Синхронный/Qt контекст или побочный поток
#     if threading.current_thread() is threading.main_thread():
#         for sig in (signal.SIGINT, signal.SIGTERM):
#             signal.signal(sig, smart_exit)
#     else:
#         atexit.register(lambda: smart_exit(None, None))


from agio.core.config import config
_emit('core.app.config_loaded', {'config': config})
_emit('core.app.on_startup')
logger.debug('Core init done')
