import atexit
import logging
import signal
import threading

from .events import emit as _emit
from .events import subscribe as _subscribe
from .init.init_packages import init_packages
from .init.init_plugins import init_plugins
from .utils import process_hub
from .utils import setup_logger

logger = logging.getLogger(__name__)
init_packages()
init_plugins()
_process_hub = process_hub.ProcessHub()
_subscribe('core.app.exit', _process_hub.shutdown)
_emit('core.app.logger_created', logger)


def _before_exit_event(*args):
    print()
    logger.debug('Receive exit signal')
    _emit('core.app.exit')

if threading.current_thread() is threading.main_thread():
    signal.signal(signal.SIGINT, _before_exit_event)
    signal.signal(signal.SIGTERM, _before_exit_event)
else:
    atexit.register(_before_exit_event)

_emit('core.app.on_startup')
logger.debug('Core init done')
