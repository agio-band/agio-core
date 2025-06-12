from agio.core.settings.package_settings import APackageSettings
from agio.core.settings import fields
from pydantic import BaseModel


class StorageRoot(BaseModel):
    name: str = fields.SlugField()
    path: str = fields.PathField(default='~/agio/store')


class CoreLocalSettings(APackageSettings):
    roots: list[StorageRoot] = None
