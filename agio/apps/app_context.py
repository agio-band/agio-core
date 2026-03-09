import os

from agio.tools import env_names


class AppContext:
    """
    Load context inside app TODO Move to launcher
    """
    @property
    def app_name(self):
        return os.getenv(env_names.APP_NAME, 'standalone')

    @property
    def app_groups(self):
        return os.getenv(env_names.APP_GROUPS, None)

    @property
    def app_version(self):
        return os.getenv(env_names.APP_VERSION)


def show_context():
    print('TODO: print agio context')