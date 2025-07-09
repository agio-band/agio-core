from agio.core.plugins.base.service_base import ServicePlugin, action
from agio.core.utils import get_actions


class ActionsService(ServicePlugin):
    name = 'actions'
    def execute(self, **kwargs):
        pass

    @action()
    def get_actions(self, menu_name: str, app_name: str, *args, **kwargs):
        action_group = get_actions(menu_name, app_name)
        return action_group.serialize()


