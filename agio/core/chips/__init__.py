from agio.core.chips import chips_hub as ch


chips_hub = ch.ChipHub()


def register(collection_name: str, chip_name: str = None):
    if not collection_name.strip():
        raise ValueError('Collection name is required')

    def decorator(cls):
        chips_hub.add_chip(cls, collection_name, chip_name)
        return cls

    return decorator



