from agio.core.packages.package_hub import APackageHub
from agio.core.plugins.plugin_hub import APluginHub
from agio.core.utils.app_context import AppContext
from logging import getLogger

from .utils import setup_logger

logger = getLogger(__name__)

# config
...

# run subprocess or continue?

# INSIDE WORKSPACE #

# event hub and callbacks
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
# plugins hub
logger.debug('Init plugins...')
plugin_hub = APluginHub(package_hub)
logger.debug(f'Loaded plugins: {plugin_hub.plugins_count}')
