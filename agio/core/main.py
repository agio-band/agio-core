import signal
from logging import getLogger

from agio.core.packages.package_hub import APackageHub
from agio.core.plugins.plugin_hub import APluginHub
from agio.core.utils.app_context import AppContext
from agio.core.api import client
from agio.core.exceptions import NotAuthorizedError
from agio.core.utils import setup_logger
from agio.core.events import emit, register_callbacks

logger = getLogger(__name__)

# auth
# server settings if workspace is defined
if not client.is_logged_in():
    logger.warning('User not authorized')
    # raise NotAuthorizedError
# app context
app_context = AppContext()
# packages hub
logger.debug('Init packages...')
package_hub = APackageHub()
logger.debug(f'Loaded packages: {package_hub.packages_count}')
# load package callbacks
callback_paths = package_hub.collect_callbacks()
register_callbacks(callback_paths)
emit('core.app.logger_created', logger)
# now we can execute callbacks
for pkg in package_hub.iter_packages():
    emit('core.app.package_loaded', pkg)
# init plugins hub
logger.debug('Init plugins...')
plugin_hub = APluginHub(package_hub)
# collect plugins
plugin_hub.collect_plugins()
for plg in plugin_hub.iter_plugins():
    emit('core.app.plugin_loaded', plg)
logger.debug(f'Loaded plugins: {plugin_hub.plugins_count}')
# core init done

# register callbacks for event core.app.exit to correct finalize you services

def _before_exit_event(*args):
    print()
    logger.debug('Receive exit signal')
    emit('core.app.exit')

signal.signal(signal.SIGINT, _before_exit_event)
signal.signal(signal.SIGTERM, _before_exit_event)

emit('core.app.startup', app_context)
logger.debug('Core init done')
