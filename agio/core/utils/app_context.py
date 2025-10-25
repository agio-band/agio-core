import os


class AppContext:
    """
    Load context inside app TODO Move to launcher
    """
    @property
    def app_name(self):
        return os.getenv('AGIO_APP_NAME', 'standalone')

    @property
    def app_group(self):
        return os.getenv('AGIO_APP_GROUPS', None)


def show_context():
    print('TODO: print agio context')