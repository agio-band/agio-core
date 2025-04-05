from pathlib import Path
import click
import logging
from agio.core.plugins.base.command_base_plugin import ACommand, AGroupCommand
from agio.core.packages import package_tools

logger = logging.getLogger(__name__)


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
        click.argument("path",
                        type=click.Path(exists=True, dir_okay=True, resolve_path=True),
                        default=Path.cwd().absolute().as_posix(),
                        metavar='[PACKAGE_PATH]'
                       ),
    ]

    def execute(self, path: str|Path):
        """
        PATH: path to package repository
        """
        logger.info(f"Build package {path}")
        package_tools.build_package(path)


class PackageReleaseCommand(ACommand):
    command_name = "release"
    arguments = [
        click.argument('version'),
        click.argument("path",
                     type=click.Path(exists=True, dir_okay=True, resolve_path=True),
                     default=Path.cwd().absolute().as_posix()),
    ]

    def execute(self, version: str, path: str):
        print(f"Make package release {version} in {path}")


class PackageCommandGroup(AGroupCommand):
    command_name = "pkg"
    commands = [PackageNewCommand, PackageBuildCommand, PackageReleaseCommand]
    help = 'Manage packages'
    # invoke_without_command = True

    # def execute(self, *args, **kwargs):
    #     print('Empty command executed: Package command')