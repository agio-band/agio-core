from agio.core.settings.package_settings import APackageSettings
from agio.core.settings import fields
from pydantic import BaseModel


class RootModel(BaseModel):
    name: str
    path_pattern: str


class Settings(APackageSettings):
    roots: list[RootModel]

