from abc import abstractmethod
from pathlib import Path

from agio.core.plugins.base_app_api import ApplicationAPIBasePlugin


class SceneAPIBasePlugin(ApplicationAPIBasePlugin):
    """
    Base class for any DCC scene implementation
    """
    __is_base_plugin__ = True
    namespace = 'scene'

    @abstractmethod
    def open(self, filename: str|Path, *kwargs):
        pass

    @abstractmethod
    def close(self, **kwargs):
        pass

    @abstractmethod
    def save(self, filename: str|Path = None):
        pass

    @abstractmethod
    def save_as(self, filename: str|Path = None):
        pass

    @abstractmethod
    def get_path(self) -> str:
        pass

    @abstractmethod
    def is_modified(self) -> bool:
        pass

    @abstractmethod
    def import_file(self, filename: str|Path, **kwargs):
        pass

    @abstractmethod
    def export_file(self, filename: str|Path, **kwargs) -> bool:
        pass

