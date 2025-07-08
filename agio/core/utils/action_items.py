from dataclasses import dataclass


@dataclass(frozen=True)
class ActionItem:
    name: str
    label: str
    icon: str
    order: str
    group: str
    menu_name: list[str]
    app_name: list[str]
    action: str
    args: list
    kwargs: dict

    def serialize(self) -> dict:
        return {
            'type': 'item',
            'name': self.name,
            'label': self.label,
            'icon': self.icon,
            'order': self.order,
            'group': self.group,
            'menu_name': self.menu_name,
            'app_name': self.app_name,
            'action': self.action,
            'args': self.args,
            'kwargs': self.kwargs,
        }

    @classmethod
    def get_fields(cls) -> list:
        return cls.__match_args__



class DividerItem:
    # TODO
    def serialize(self) -> dict:
        return {"type": "divider"}


class GroupItem:
    """Menu or group of items"""
    # TODO
    def __init__(self, name: str, label: str, items: list = None) -> None:
        self.name = name
        self.label = label
        self._items = []
        if items is not None:
            self.add_items(*items)

    def add_items(self, *items: ActionItem) -> None:
        self._items.extend(items)

    def serialize(self) -> dict:
        return {
            'name': self.name,
            'label': self.label,
            'items': self._items,
            'type': 'group',
            'group': self.name,
        }
