import logging
import signal

from .events import emit as _emit, subscribe as _subscribe
from .init.init_packages import init_packages
from .init.init_plugins import init_plugins
from .utils import setup_logger
from .utils.process_hub import ProcessHub

__all__ = [
    'package_hub',
    'plugin_hub',
    'process_hub'
]


logger = logging.getLogger(__name__)

package_hub = init_packages()
plugin_hub = init_plugins(package_hub)
process_hub = ProcessHub()
_subscribe('core.app.exit', process_hub.shutdown)

def _before_exit_event(*args):
    print()
    logger.debug('Receive exit signal')
    _emit('core.app.exit')


signal.signal(signal.SIGINT, _before_exit_event)
signal.signal(signal.SIGTERM, _before_exit_event)

_emit('core.app.on_startup')
logger.debug('Core init done')