import click

from agio.core.plugins.base_command import ACommandPlugin
from agio.core.utils import actions
from agio.core.utils import get_actions


class ActionCommand(ACommandPlugin):
    name = 'action_cmd'
    command_name = 'action'
    allow_extra_args = True
    arguments = [
        click.argument('action'),
        # click.argument('args', nargs=-1) -> use __extra_args__ instead
    ]
    help = 'Execute any action'

    def execute(self, action, **kwargs):
        action_args, action_kwargs = self.parse_extra_args(kwargs)
        action_func = actions.get_action_func(action)
        result = action_func(*action_args, **action_kwargs)
        return result


class GetActionsCommand(ACommandPlugin):
    name = 'get_actions_cmd'
    command_name = 'get-actions'
    allow_extra_args = True
    allow_write_output_to_custom_pipe = True    # temporary forced write to custom pipe

    arguments = (
        click.option('-m', '--menu-name', default=None, help='Manu Name'),
        click.option('-a', '--app-name', default=None, help='App Name'),
    )

    def execute(self, menu_name, app_name, **kwargs):
        action_group = get_actions(menu_name, app_name)
        all_actions = action_group.serialize()
        return all_actions

