import code
import atexit
import os
# import readline

from agio.core.plugins.base_command import ACommandPlugin
from agio.tools import local_dirs
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
    py_history_path = local_dirs.config_dir(".pyhistory").as_posix()

    def save_py_session(path=py_history_path):
        readline.write_history_file(path)

    if os.path.exists(py_history_path):
        readline.read_history_file(py_history_path)
    atexit.register(save_py_session)
    readline.parse_and_bind('tab: complete')
    del save_py_session, py_history_path

    ic = code.InteractiveConsole(locals=namespace)
    try:
        ic.interact('agio Debug Console Loaded', '')
    except (SystemExit, KeyboardInterrupt):
        print('CLOSE CONSOLE...')
