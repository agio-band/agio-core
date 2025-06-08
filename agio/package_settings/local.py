from agio.core.settings.package_settings import APackageSettings
from agio.core.settings import fields


class CoreLocalSettings(APackageSettings):
    show_notifications: bool = True
    storage_root: str = fields.PathField(default='~/agio_store')
