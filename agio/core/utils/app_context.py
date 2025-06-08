import os


class AppContext:

    @property
    def app_name(self):
        return os.getenv('AGIO_APP_NAME', 'standalone')

    @property
    def app_group(self):
        return os.getenv('AGIO_APP_GROUP', None)


