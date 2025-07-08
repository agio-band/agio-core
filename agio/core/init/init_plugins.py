import logging

from agio.core.events import emit
from agio.core.plugins.plugin_hub import APluginHub

logger = logging.getLogger(__name__)


def init_plugins(package_hub):
    # init plugins hub
    logger.debug('Initializing plugin hub...')
    plugin_hub = APluginHub(package_hub)
    # collect plugins
    plugin_hub.collect_plugins()
    for plg in plugin_hub.iter_plugins():
        emit('core.app.plugin_loaded', plg)
    logger.debug(f'Loaded plugins: {plugin_hub.plugins_count}')
    return plugin_hub