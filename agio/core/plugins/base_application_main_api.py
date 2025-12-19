import sys
from abc import abstractmethod

from agio.core.plugins.base_app_api import ApplicationAPIBasePlugin


class MainAppAPIBase(ApplicationAPIBasePlugin):
    namespace = 'main'  # can be same for other app

    @abstractmethod
    def get_py_executable(self):
        pass
