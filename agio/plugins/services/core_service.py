from agio.core.api import client
from agio.core.plugins.base.service_base import ServicePlugin, action
import signal
import os


class CoreService(ServicePlugin):
    name = 'core_actions'
    def execute(self, **kwargs):
        pass

    @action(menu_name='tray.main_menu', app_name='desk', order=100)
    def exit(self):
        os.kill(os.getpid(), signal.SIGINT)

    @action(menu_name='tray.main_menu', app_name='desk', order=99)
    def login(self):
        client.login()

    @action(menu_name='tray.main_menu', app_name='desk', order=98)
    def login(self):
        client.logout()
