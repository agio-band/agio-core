import atexit
import logging
import signal
import threading

from agio.core import setup_logger
from agio.core.events import emit as _emit, subscribe as _subscribe
from agio.core.init.init_packages import init_packages
from agio.core.init.init_plugins import init_plugins
from agio.tools import process_hub

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
    signal.signal(signum, signal.SIG_DFL)
    signal.raise_signal(signum)


if threading.current_thread() is threading.main_thread():
    signal.signal(signal.SIGINT, _before_exit_event)
    signal.signal(signal.SIGTERM, _before_exit_event)
else:
    atexit.register(_before_exit_event)


# _emit('core.app.config_loaded', {'config': config})
_emit('core.app.on_startup')
logger.debug('Core init done')
