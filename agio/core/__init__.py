import logging
import signal

from .utils import setup_logger
from .events import emit
from .init.init_plugins import init_plugins
from .init.init_packages import init_packages

__all__ = [
    'package_hub',
    'plugin_hub',
    'process_hub'
]

from .utils.process_hub import ProcessHub

logger = logging.getLogger(__name__)

package_hub = init_packages()
plugin_hub = init_plugins(package_hub)
process_hub = ProcessHub()

def _before_exit_event(*args):
    print()
    logger.debug('Receive exit signal')
    emit('core.app.exit')


signal.signal(signal.SIGINT, _before_exit_event)
signal.signal(signal.SIGTERM, _before_exit_event)

emit('core.app.on_startup')
logger.debug('Core init done')