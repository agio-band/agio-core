from agio.core.settings.fields.generic_fields import StringField


class JSONField(StringField):
    default_widget = 'JSONEditorWidget'


class MarkdownField(StringField):
    default_widget = 'MarkdownEditorWidget'
