from agio.core.packages.package_hub import APackageHub
from agio.core.plugins.plugin_hub import APluginHub
from agio.core.utils.app_context import AppContext
from logging import getLogger
# import local config to init values
from .utils import setup_logger

logger = getLogger(__name__)

# load local config
...
# init event hub and load default callbacks
...
# auth
...
# server configs
...
# app context
app_context = AppContext()
# load workspace settings if exists
...
# packages hub
logger.debug('Init packages...')
package_hub = APackageHub()
logger.debug(f'Loaded packages: {package_hub.packages_count}')
# load package callbacks
...
# call special callbacks (setup logging, workspace config, etc.)
...
# init plugins hub
logger.debug('Init plugins...')
plugin_hub = APluginHub(package_hub)
# collect plugins
...
# init plugins
...
logger.debug(f'Loaded plugins: {plugin_hub.plugins_count}')
# core init done
logger.debug('Core init done')
