import logging

from agio.core.events import register_callbacks, emit
from agio.core.workspaces import package_hub

logger = logging.getLogger(__name__)


def init_packages():
    logger.debug('Initializing package hub...')
    ph = package_hub.APackageHub()
    # load package callbacks
    callback_paths = ph.collect_callbacks()
    register_callbacks(callback_paths)
    # now we can execute callbacks
    for pkg in ph.iter_packages():
        emit('core.app.package_loaded', {'package': pkg})
    emit('core.app.all_packages_loaded', {'package_hub': ph})
    logger.debug('Loaded packages: %s', ph.packages_count)
    return ph
