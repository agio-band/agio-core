from agio.core.settings.fields.generic_fields import StringField


class JSONField(StringField):
    field_type = list|dict|str
    default_widget = 'JSONEditorWidget'


class MarkdownField(StringField):
    default_widget = 'MarkdownEditorWidget'
