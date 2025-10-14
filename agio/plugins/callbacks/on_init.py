from agio.core.events import callback, AEvent
import logging

logger = logging.getLogger(__name__)


@callback('core.app.on_startup')
def on_app_startup(event: AEvent):
    logger.debug('Code initializing done')
