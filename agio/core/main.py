from logging import getLogger

from agio.core.packages.package_hub import APackageHub
from agio.core.plugins.plugin_hub import APluginHub
from agio.core.utils.app_context import AppContext
from agio.core.api import client
from agio.core.exceptions import NotAuthorizedError
# import local config to init values
from agio.core.utils import setup_logger
from agio.core.events import emit, register_callbacks

logger = getLogger(__name__)

# auth
# server settings if workspace is defined
if not client.is_logged_in():
    logger.warning('User not authorized')
# app context
app_context = AppContext()
# packages hub
logger.debug('Init packages...')
package_hub = APackageHub()
logger.debug(f'Loaded packages: {package_hub.packages_count}')
# load package callbacks
callback_paths = package_hub.collect_callbacks()
register_callbacks(callback_paths)
emit('agio.init.logger_created', logger)
# now we can execute callbacks
for pkg in package_hub.iter_packages():
    emit('agio.init.package_loaded', pkg)
# init plugins hub
logger.debug('Init plugins...')
plugin_hub = APluginHub(package_hub)
# collect plugins
plugin_hub.collect_plugins()
for plg in plugin_hub.iter_plugins():
    emit('agio.plugins.plugin_loaded', plg)
logger.debug(f'Loaded plugins: {plugin_hub.plugins_count}')
# core init done
emit('agio.init.done', app_context)
logger.debug('Core init done')
