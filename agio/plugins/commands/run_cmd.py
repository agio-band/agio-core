import sys

from  agio.core.cli.tools import Env
import click
from agio.core.plugins.base_command import ACommandPlugin
from agio.core.utils.process_utils import start_process


class RunCommand(ACommandPlugin):
    name = 'run_cmd'
    command_name = 'run'
    arguments = [
        click.option("-e", "--env", help='Custom Environments', type=Env(), multiple=True),
        click.option("-w", "--cwd", help='Workdir', type=click.Path(exists=True, dir_okay=True, resolve_path=True)),
        click.argument('command', nargs=-1, type=click.UNPROCESSED),
    ]
    # click options to allow unknown arguments
    context_settings = dict(
        ignore_unknown_options=True,
        allow_extra_args=True,
    )
    help = 'Run command in current workspace context'

    def execute(self, env: list = None, cwd: str = None, command: tuple = None):
        if env or cwd:
            if '--' not in sys.argv:
                raise Exception('Split arguments and command with double dash to separate external arguments. '
                                f'Example: agio run --workdir ~/test --env KEY=VALUE -- {" ".join(command)}')
        if not command:
            raise Exception('Command is required')
        if env:
            env = dict(env)
        start_process(command, envs=env, workdir=cwd, replace=True)
