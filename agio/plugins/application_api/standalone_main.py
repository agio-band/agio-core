import sys
from agio.core.plugins.base_application_main_api import MainAppAPIBase


class StandaloneMainAppAPI(MainAppAPIBase):
    name = 'main_app_api'   # can be same for other app
    namespace = 'main'

    def get_py_executable(self):
        return sys.executable
