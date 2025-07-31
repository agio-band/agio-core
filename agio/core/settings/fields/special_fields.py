from agio.core.settings.fields.base_field import BaseField


class PluginSelectField(BaseField):
    field_type = str

    def __init__(self, plugin_type: str, **kwargs):
        if not plugin_type:
            raise ValueError("Plugin type must be specified")
        super().__init__(**kwargs)
        self.plugin_type = plugin_type

    def get_additional_info(self):
        from agio.core import plugin_hub

        names = [(plg.get_label(), plg.name) for plg in plugin_hub.get_plugins_by_type(self.plugin_type)]
        info = super().get_additional_info()
        info['enum_options'] = names
        return info