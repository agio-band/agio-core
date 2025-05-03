from agio.core.settings.fields.base_field import BaseField


class StringField(BaseField):
    field_type = str


class IntField(BaseField):
    field_type = int


class FloatField(BaseField):
    field_type = float


class BoolField(BaseField):
    field_type = bool
