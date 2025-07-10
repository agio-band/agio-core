import os
import signal

from agio.core import emit
from agio.core.api import client
from agio.core.plugins.base.service_base import ServicePlugin, make_action


class CoreService(ServicePlugin):
    name = 'core'

    @make_action(label='Log Out',
                 menu_name='tray.main_menu',
                 app_name='desk',
                 order=98,
                 is_visible_callback=client.is_logged_in)
    def logout(self, *args, **kwargs):
        emit('core.before_logout')
        client.logout()
        emit('core.on_logout')

    @make_action(label='Log In',
                 menu_name='tray.main_menu',
                 app_name='desk',
                 order=99,
                 is_visible_callback=lambda: not client.is_logged_in())
    def login(self, *args, **kwargs):
        emit('core.before_login')
        client.login()
        emit('core.on_login')

    @make_action(menu_name='tray.main_menu',
                 app_name='desk',
                 order=100)
    def exit(self, *args, **kwargs):
        os.kill(os.getpid(), signal.SIGINT)
