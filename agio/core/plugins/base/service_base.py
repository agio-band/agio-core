from threading import Thread, Event
from agio.core.plugins.mixins import BasePluginClass
from agio.core.plugins.plugin_base import APlugin


class AServicePlugin(BasePluginClass, APlugin):
    plugin_type = 'service'

    def __init__(self, *args, **kwargs):
        super(AServicePlugin, self).__init__(*args, **kwargs)
        self._thread = None
        self._event = Event()

    def start(self, in_thread: bool = True, **kwargs):
        if in_thread:
            self._thread = Thread(target=self.execute, **kwargs)
            self._thread.start()
        else:
            self.execute(**kwargs)

    def is_stopped(self):
        return self._event.is_set()

    def execute(self, **kwargs):
        raise NotImplementedError

    def stop(self):
        self._event.set()
        if self._thread:
            self._thread.join()
