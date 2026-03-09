import weakref

from agio.core.plugins import base_plugin
from agio.tools.paths import system_executable_extension


class ApplicationAPIBasePlugin(base_plugin.APlugin):
    __is_base_plugin__ = True
    plugin_type = 'application_api'
    namespace: str = None
    required_attrs = {'namespace'}

    def __init__(self, app, *args, **kwargs):
        super().__init__(app, *args, **kwargs)
        self._app = weakref.ref(app)

    def __str__(self):
        return self.name

    def __repr__(self):
        return f'<{self.__class__.__name__} "{self.name}">'

    @property
    def app(self):
        return self._app()

    @property
    def exec_ext(self):
        return system_executable_extension()