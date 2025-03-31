from pathlib import Path
import click
from agio.core.plugins.plugin_cmd_base import ACommand, AGroupCommand


class PackageNewCommand(ACommand):
    command_name = "new"
    arguments = [
        click.option("-p", "--path", help='Package root path, Default: $PWD',
                     type=click.Path(exists=True, dir_okay=True, resolve_path=True),
                     default=Path.cwd().absolute().as_posix()),
    ]

    def execute(self, path: str):
        print(f"Create new package in {path}")


class PackageBuildCommand(ACommand):
    command_name = "build"
    arguments = [
        click.option("-p", "--path", help='Package root path, Default: $PWD',
                     type=click.Path(exists=True, dir_okay=True, resolve_path=True),
                     default=Path.cwd().absolute().as_posix()),
    ]

    def execute(self, path: str):
        print(f"Build package in {path}")


class PackagePublishCommand(ACommand):
    command_name = "publish"
    arguments = [
        click.option("-p", "--path", help='Package root path, Default: $PWD',
                     type=click.Path(exists=True, dir_okay=True, resolve_path=True),
                     default=Path.cwd().absolute().as_posix()),
    ]

    def execute(self, path: str):
        print(f"Publish package in {path}")


class PackageCommandGroup(AGroupCommand):
    command_name = "pkg"
    commands = [PackageNewCommand, PackageBuildCommand, PackagePublishCommand]
    help = 'Manage packages'
    # invoke_without_command = True

    # def execute(self, *args, **kwargs):
    #     print('Empty command executed: Package command')