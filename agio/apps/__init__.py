import logging

from agio.core.settings import get_local_settings
from agio.core.plugins import plugin_hub
from agio_apps.utils.app_launcher import AApplicationLauncher
from agio_apps.utils.app_hub import ApplicationHub

logger = logging.getLogger(__name__)

app_hub = ApplicationHub()
app = None # TODO: current context app


def get_app_list():
    local_settings = get_local_settings()
    apps_config = sorted(local_settings.get('agio_apps.applications', []), key=lambda a: (a.name, a.version))
    if not apps_config:
        return
    all_app_plugins = list(plugin_hub.APluginHub.instance().get_plugins_by_type('app_launcher'))
    if not all_app_plugins:
        logger.warning('No plugins found for any applications')
        return
    for app_plg in all_app_plugins:
        conf_list = [x for x in apps_config if x.name == app_plg.app_name]
        for c in conf_list:
            yield AApplicationLauncher(app_plg, c.version, c)
