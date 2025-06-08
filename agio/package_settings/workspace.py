from agio.core.settings.package_settings import APackageSettings
from agio.core.settings import fields
from pydantic import BaseModel

from agio.core.settings.validators import RegexValidator


class RootModel(BaseModel):
    name: str = fields.StringField(validators=[RegexValidator(r"[a-zA-Z][a-zA-Z0-9_\-]*]")])
    path_pattern: fields.PathPatternField


class CoreWorkspaceSettings(APackageSettings):
    roots: list[RootModel]

