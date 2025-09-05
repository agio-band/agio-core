from typing import Final, Callable

from agio.core.plugins.base_plugin import APlugin
from agio.core.plugins.mixins import BasePluginClass


class ContextArgsPlugin(BasePluginClass, APlugin):
    plugin_type: Final[str] = 'extra_context_args'

    def get_args(self) -> list[Callable]:
        raise NotImplementedError

    def execute(self, launch_kwargs: dict = None):
        raise NotImplementedError()
