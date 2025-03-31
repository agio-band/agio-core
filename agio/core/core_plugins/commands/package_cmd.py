from pathlib import Path

import click

from agio.core.plugins.plugin_cmd_base import ACommand, SubCommand


class PackageNewCommand(SubCommand):
    command_name = "new"
    arguments = [
        click.option("-p", "--path", help='Package root path, Default: $PWD',
                     type=click.Path(exists=True, dir_okay=True, resolve_path=True),
                     default=Path.cwd().absolute().as_posix()),
    ]

    def execute(self, path: str):
        print(f"Create new package in {path}")


class PackageBuildCommand(SubCommand):
    command_name = "build"
    arguments = [
        click.option("-p", "--path", help='Package root path, Default: $PWD',
                     type=click.Path(exists=True, dir_okay=True, resolve_path=True),
                     default=Path.cwd().absolute().as_posix()),
    ]

    def execute(self, path: str):
        print(f"Build package in {path}")


class PackagePublishCommand(SubCommand):
    command_name = "publish"
    arguments = [
        click.option("-p", "--path", help='Package root path, Default: $PWD',
                     type=click.Path(exists=True, dir_okay=True, resolve_path=True),
                     default=Path.cwd().absolute().as_posix()),
    ]

    def execute(self, path: str):
        print(f"Publish package in {path}")


class PackageCommand(ACommand):
    command_name = "package"
    subcommands = [PackageNewCommand, PackageBuildCommand, PackagePublishCommand]
    # invoke_without_command = True

    # def execute(self, *args, **kwargs):
    #     print('Empty command executed: Package command')