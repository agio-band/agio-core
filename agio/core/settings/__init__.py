from .fields.base_field import BaseField
from .fields.compaund_fields import ListField, SetField, TupleField, DictField
from .fields.extended_fields import (
    DateTimeField,
    FrameRangeField,
    VectorField,
    Vector4Field,
    Vector3Field,
    Vector2Field,
    RGBColorField
)
from .fields.generic_fields import StringField, IntField, BaseField, FloatField
from .package_settings import APackageSettings
from .collector import read_local_settings_values
from .settings_hub import LocalSettingsHub, WorkspaceSettingsHub
from ..workspace.workspace import AWorkspace


def get_local_settings() -> LocalSettingsHub:
    # read local settings from files
    local_settings = read_local_settings_values()
    # create local settings instance with applied values
    return LocalSettingsHub(local_settings)


def get_workspace_settings() -> WorkspaceSettingsHub:
    # create workspace instance
    ws = AWorkspace.current()
    if not ws:
        raise RuntimeError('Workspace is not initialized')
    # get workspace settings from server
    settings = {}
    # create workspace settings instance with applied values
    return WorkspaceSettingsHub(settings)
