import logging
import signal

from .events import subscribe as _subscribe
from .events import emit as _emit
from .init.init_packages import init_packages
from .init.init_plugins import init_plugins
from .utils import setup_logger
from .utils import process_hub


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


signal.signal(signal.SIGINT, _before_exit_event)
signal.signal(signal.SIGTERM, _before_exit_event)

_emit('core.app.on_startup')
logger.debug('Core init done')
