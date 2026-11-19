import click

import agio.core.actions
from agio.core.actions import get_actions
from agio.core.plugins.base_command import ACommandPlugin


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
        action_func = agio.core.actions.get_action_func(action)
        result = action_func(*action_args, **action_kwargs)
        print(result, flush=True)
        return result


class GetActionsCommand(ACommandPlugin):
    name = 'get_actions_cmd'
    command_name = 'get-actions'
    help = 'Getting all actions as JSON'
    allow_extra_args = True
    allow_write_output_to_custom_pipe = True    # temporary forced write to custom pipe

    arguments = (
        click.option('-m', '--menu-name', default=None, help='Manu Name'),
        click.option('-a', '--app-name', default=None, help='App Name'),
        click.option('--app-group', default=None, help='App Group'),
        click.option('--app-version', default=None, help='App version requirement, for example ">=10,<15"'),
        click.option('--action-group', default=None, help='Action Group'),
    )

    def execute(self, menu_name, app_name, app_group, app_version, action_group, **kwargs):
        group_item = get_actions(
            menu_name,
            app_name,
            app_group=app_group,
            app_version=app_version,
            action_group=action_group,
        )
        all_actions = group_item.serialize()
        return all_actions

