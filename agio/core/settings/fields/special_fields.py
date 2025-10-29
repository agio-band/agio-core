from agio.core.settings.fields.base_field import BaseField
from agio.core.plugins import plugin_hub


class PluginSelectField(BaseField):
    field_type = str

    def __init__(self, plugin_type: str, **kwargs):
        if not plugin_type:
            raise ValueError("Plugin type must be specified")
        super().__init__(**kwargs)
        self.plugin_type = plugin_type

    def get_additional_info(self):

        names = [{
            'label': plg.get_label(),
            'value': plg.name
        } for plg in plugin_hub.APluginHub.instance().get_plugins_by_type(self.plugin_type)]
        info = super().get_additional_info()
        info['enum_options'] = names
        return info