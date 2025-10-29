import logging

from agio.core.events import emit
from agio.core.plugins import plugin_hub
from agio.core.workspaces import package_hub
from agio.tools import context

logger = logging.getLogger(__name__)


def init_plugins(pkg_hub: package_hub.APackageHub = None):
    # get workspaces hub
    pkg_hub = pkg_hub or package_hub.APackageHub.instance(False)
    if not pkg_hub:
        raise RuntimeError('Package hub not initialized yet')
    # init plugins hub
    logger.debug(f'Initializing plugin hub for app {context.app_name}...')
    plg_hub = plugin_hub.APluginHub(pkg_hub)
    # collect plugins
    plg_hub.collect_plugins()
    for plg in plg_hub.iter_plugins():
        emit('core.app.plugin_loaded', plg)
    logger.debug(f'Loaded plugins: {plg_hub.plugins_count}')
    return plg_hub