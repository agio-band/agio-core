from agio.core.settings.fields.base_field import BaseField
from agio.core.plugins import plugin_hub
from agio.core.chips import chips_hub


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


class ChipSelectField(BaseField):
    field_type = str
    def __init__(self, chip_collection_name: str, **kwargs):
        if not chip_collection_name:
            raise ValueError("Chip type must be specified")
        super().__init__(**kwargs)
        self.chip_collection_name = chip_collection_name

    def get_additional_info(self):
        collection = chips_hub.collections.get(self.chip_collection_name)
        chip_names = [{
            'label': chips_hub.get_chip_name(chip),
            'value': chips_hub.get_chip_name(chip)
        } for chip in collection]
        info = super().get_additional_info()
        info['enum_options'] = chip_names
        return info