import logging

from agio.core.events import register_callbacks, emit
from agio.core.utils.package_hub import APackageHub

logger = logging.getLogger(__name__)


def init_packages():
    logger.debug('Initializing package hub...')
    package_hub = APackageHub()
    # load package callbacks
    callback_paths = package_hub.collect_callbacks()
    register_callbacks(callback_paths)
    emit('core.app.logger_created', logger)
    # now we can execute callbacks
    for pkg in package_hub.iter_packages():
        emit('core.app.package_loaded', pkg)
    logger.debug('Loaded packages: %s', package_hub.packages_count)
    return package_hub
