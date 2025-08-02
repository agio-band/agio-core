from agio.core.events import callback
import logging

logger = logging.getLogger(__name__)


@callback('core.app.on_startup')
def on_app_startup():
    logger.debug('Code initializing done')
