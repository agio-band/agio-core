from agio.core.settings.fields.base_field import BaseField


class PluginSelectField(BaseField):
    def __init__(self, plugin_type: str, **kwargs):
        if not plugin_type:
            raise ValueError("Plugin type must be specified")
        from agio.core import plugin_hub
        names = [plg.get_label() for plg in plugin_hub.get_plugins_by_type(plugin_type)]
        kwargs['enum'] = names
        super().__init__(**kwargs)
