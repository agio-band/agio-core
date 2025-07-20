import logging

from agio.core.events import emit
from agio.core.utils.plugin_hub import APluginHub
from agio.core.utils import context

logger = logging.getLogger(__name__)


def init_plugins(package_hub):
    # init plugins hub
    logger.debug(f'Initializing plugin hub for app {context.app_name}...')
    plugin_hub = APluginHub(package_hub)
    # collect plugins
    plugin_hub.collect_plugins()
    for plg in plugin_hub.iter_plugins():
        emit('core.app.plugin_loaded', plg)
    logger.debug(f'Loaded plugins: {plugin_hub.plugins_count}')
    return plugin_hub