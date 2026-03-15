import code

from agio.core.plugins.base_command import ACommandPlugin
import click

class ShellCommand(ACommandPlugin):
    name = 'shell_cmd'
    command_name = 'shell'
    arguments = [
        click.option('-a', '--agio-imports', is_flag=True, default=False, help='Import core modules and objects'),
    ]
    help = 'Settings info'

    def execute(self, agio_imports: bool = False):

        ns = {}
        console(ns)


def console(namespace: dict = None):
    ic = code.InteractiveConsole(locals=namespace)
    try:
        ic.interact('agio Debug Console Loaded', '')
    except (SystemExit, KeyboardInterrupt):
        print('CLOSE CONSOLE...')
