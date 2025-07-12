from agio.core.settings import APackageSettings, StringField


class CoreSettings(APackageSettings):
    show_notifications: bool = True
    workspaces_root: str = ''

