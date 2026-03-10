import logging

from agio.core.settings import get_local_settings
from agio.core.plugins import plugin_hub
from agio.apps.launcher import AApplicationLauncher
from agio.apps.app_hub import ApplicationHub
from .context_app import ContextApp

__all__ = ['app', 'app_hub', 'get_app_config', 'get_registered_apps', 'get_app_list']


logger = logging.getLogger(__name__)

app_hub = ApplicationHub()
app = ContextApp()


def get_app_config():
    local_settings = get_local_settings()
    apps_config = sorted(local_settings.get('agio_core.applications', []), key=lambda a: (a.name, a.version))
    return apps_config


def get_registered_apps():
    return list(plugin_hub.APluginHub.instance().get_plugins_by_type('app_launcher'))


def get_app_list():
    apps_config = get_app_config()
    if not apps_config:
        return
    all_app_plugins = get_registered_apps()
    if not all_app_plugins:
        logger.warning('No plugins found for any applications')
        return
    for app_plg in all_app_plugins:
        conf_list = [x for x in apps_config if x.name == app_plg.app_name]
        for c in conf_list:
            yield AApplicationLauncher(app_plg, c.version, c)
