import logging
from threading import Event
from typing import Iterable

from agio.core.events import subscribe, unsubscribe
from agio.tools.singleton import Singleton
from agio.core.plugins import plugin_hub


class AServiceHub(metaclass=Singleton):
    """
    This context manager starts services on ENTER to context and stop it on EXIT
    """
    _registered_services = []

    def __init__(self, service_list: Iterable[str], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.stop_event = Event()
        self._active_services = []
        self.service_list = service_list
        subscribe('core.app.exit', self.stop)

    def __enter__(self, **kwargs):
        self.start_services(**kwargs)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop_services()

    def stop(self, *args, **kwargs):
        self.stop_event.set()
        unsubscribe(self.stop)

    def is_stopped(self):
        return self.stop_event.is_set()

    def start_services(self, **kwargs):
        already_registered = [s for s in self.service_list if s in self._registered_services]
        if already_registered:
            raise Exception('Service already running: {}'.format(already_registered))
        names_to_register = set(self.service_list)
        services = []
        for service in plugin_hub.APluginHub.instance().iter_plugins('service'):
            if service.name in names_to_register:
                if service.name in self._registered_services:
                    raise Exception('Service already registered: {}'.format(service.name))
                services.append(service)
        found_names = [s.name for s in services]
        if missing := set(found_names) - set(self.service_list):
            raise Exception('Service not installed: {}'.format(', '.join(missing)))

        for srv in services:
            srv.start()
            self._active_services.append(srv)
            self._registered_services.append(srv.name)

    def stop_services(self):
        for service in self._active_services:
            try:
                service.stop()
            except Exception as e:
                logging.exception('Failed to stop plugin: {}'.format(e))
            self._registered_services.remove(service.name)
        self._active_services.clear()
