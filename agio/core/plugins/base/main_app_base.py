import logging
from threading import Event

from agio.core.events import subscribe, unsubscribe
from agio.core.plugins.mixins import BasePluginClass
from agio.core.plugins.plugin_base import APlugin


class AMainAppPlugin(BasePluginClass, APlugin):
    """
    To start main app use command `agio startapp appname`
    """
    plugin_type = 'main_app'
    services = set()
    _registered_services = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.stop_event = Event()
        self._active_services = []
        subscribe('core.app.exit', self.stop)

    def execute(self, **kwargs):
        raise NotImplementedError

    def start(self, **kwargs):
        print('Start main app plugin', self.name)
        self.before_start(**kwargs)
        try:
            self.execute(**kwargs)
        finally:
            self.on_exist()
            print('Stop main app plugin', self.name)

    def stop(self, *args, **kwargs):
        self.stop_event.set()
        unsubscribe(self.stop)

    def is_stopped(self):
        return self.stop_event.is_set()

    def before_start(self, **kwargs):
        from agio.core.main import plugin_hub

        already_registered = [s for s in self.services if s in self._registered_services]
        if already_registered:
            raise Exception('Plugins already initialized: {}'.format(already_registered))
        names_to_register = set(self.services)
        services = []
        for plugin in plugin_hub.iter_plugins('service'):
            if plugin.name in names_to_register:
                if plugin.name in self._registered_services:
                    raise Exception('Plugins already registered: {}'.format(plugin.name))
                services.append(plugin)
        for srv in services:
            srv.start()
            self._active_services.append(srv)
            self._registered_services.append(srv.name)

    def on_exist(self):
        for plugin in self._active_services:
            try:
                plugin.stop()
            except Exception as e:
                logging.exception('Failed to stop plugin: {}'.format(e))
            self._registered_services.remove(plugin.name)
        self._active_services.clear()
