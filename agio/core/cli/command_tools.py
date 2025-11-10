import re

from agio.core.plugins import plugin_hub
from agio.core.plugins.base_command import AbstractCommandPlugin


def execute_command(command, *args, **kwargs):
    """Execute command from code
    execute_command('info packages')
    execute_command('ws install', 'WS-ID-HERE')
    """
    main_command, sub_command = parse_command(command)
    if main_command == 'agio':
        raise NameError('Do not include "agio" to command, use command name directly. '
                        'Example: execute_command("info")')
    cmd = find_command_plugin(main_command, sub_command)
    return cmd.execute(*args, **kwargs)


def parse_command(command: str|list|tuple) -> tuple[str, str|None]:
    if isinstance(command, (list, tuple)):
        if len(command) > 2:
            raise ValueError(f'Supported only single command or command+subcommand. To many names in {command}')
        main_command, sub_command = command
    else:
        solved = re.search(r"(\w+)\s?(\w+)?", command)
        if not solved:
            raise ValueError(f'Wrong command format {command}')
        main_command, sub_command = solved.groups()
    return main_command, sub_command


def find_command_plugin(main_command: str, sub_command: str = None):
    main_cmd_plugin: AbstractCommandPlugin = None
    for cmd in plugin_hub.APluginHub.instance().iter_plugins('command'):
        if cmd.command_name == main_command:
            main_cmd_plugin = cmd
            break
    if not main_cmd_plugin:
        raise NameError(f'Command plugin "{main_command}" not found')
    if sub_command:
        if not AbstractCommandPlugin.subcommands:
            raise NameError(f'Command plugin "{main_command}" has no subcommands. requested: {main_command}')
        for subcommand_plugin in AbstractCommandPlugin.subcommands:
            if subcommand_plugin.command_name == sub_command:
                return subcommand_plugin
        else:
            raise NameError(f'Subcommand "{sub_command}" not found')
    else:
        return main_cmd_plugin
