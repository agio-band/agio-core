# from .package_settings import APackageSettings
# from .workspace_settings import AWorkspaceSettings
from .fields.base_field import BaseField
from .fields.compaund_fields import ListField, SetField, TupleField, DictField
from .fields.extended_fields import DateTimeField, FrameRangeField, VectorField, Vector4Field, Vector3Field, Vector2Field, ColorField
from .fields.generic_fields import StringField, IntField, BaseField, FloatField


def collect_workspace_settings(workspace_id: str = None):
    # create workspace instance
    # get workspace settings from server
    # iterate over packages
    #   create package settings instance
    # create workspace settings instance
    pass