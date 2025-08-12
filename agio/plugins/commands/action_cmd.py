import json

from agio.core.plugins.base_command import ACommandPlugin
import click

from agio.core.utils.args_helper import parse_args_to_dict
from agio.core.utils import actions, process_utils

class ActionCommand(ACommandPlugin):
    name = 'action_cmd'
    command_name = 'action'
    context_settings = dict(ignore_unknown_options=True)
    arguments = [
        click.argument('action'),
        click.argument('args', nargs=-1)
    ]
    help = 'Execute any action'

    def execute(self, action, args: tuple|list):
        print('ACTION:', action)
        if args:
            args: dict = parse_args_to_dict(args)
        print('KWARGS:', args)
        # find action
        action_func = actions.get_action_func(action)
        # execute and get result
        result = action_func(**args)
        # write to pipe is defined
        if process_utils.pipe_is_allowed():
            with process_utils.data_pipe('w') as pipe:
                pipe.write(json.dumps(result))
        # done
        return result

