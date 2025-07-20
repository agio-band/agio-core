from agio.core.plugins.base_command import ACommandPlugin
import click

from agio.core.utils.args_helper import parse_args_to_dict


class ActionCommand(ACommandPlugin):
    name = 'action_cmd'
    command_name = 'action'
    context_settings = dict(ignore_unknown_options=True)
    arguments = [
        click.argument('action'),
        click.argument('args', nargs=-1)
    ]
    help = 'Execute any action'

    def execute(self, action, args):
        # TODO
        print(action)
        if args:
            args = parse_args_to_dict(args)
        print(args)