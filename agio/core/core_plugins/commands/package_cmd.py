from pathlib import Path

import click
import logging
from agio.core.plugins.base.base_plugin_command import ACommand, AGroupCommand
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
        click.option('-b', '--no-check-branch', is_flag=True, default=False, help='Skip branch check'),
        click.option('-c', '--no-check-commits', is_flag=True, default=False, help='Skip commits check'),
        click.option('-p', '--no-check-pushed', is_flag=True, default=False, help='Skip push check'),
        click.option('-l', '--no-cleanup', is_flag=True, default=False, help='Skip cleanup build files'),
    ]

    def execute(self, path: str|Path, **kwargs):
        """
        PATH: path to package repository
        """
        logger.info(f"Build package {path}")
        package_tools.build_package(path, **kwargs)


class PackageReleaseCommand(ACommand):
    command_name = "release"
    arguments = [
        click.option('-t', '--token'),
        click.option('-b', '--no-check-branch', is_flag=True, default=False, help='Skip branch check'),
        click.option('-c', '--no-check-commits', is_flag=True, default=False, help='Skip commits check'),
        click.option('-p', '--no-check-pushed', is_flag=True, default=False, help='Skip push check'),
        click.option('-l', '--no-cleanup', is_flag=True, default=False, help='Skip cleanup build files'),
        click.argument("path",
                     type=click.Path(exists=True, dir_okay=True, resolve_path=True),
                     default=Path.cwd().absolute().as_posix()),
    ]

    def execute(self, token: str, path: str, **kwargs):
        logger.debug(f"Make package release: {path}")
        result = package_tools.make_release(path, token=token, **kwargs)
        from pprint import pprint
        pprint(result)


class PackageRegisterCommand(ACommand):
    command_name = "register"
    arguments = [
        click.option('-t', '--token'),
        click.argument("path",
                     type=click.Path(exists=True, dir_okay=True, resolve_path=True),
                     default=Path.cwd().absolute().as_posix()),
    ]

    def execute(self, token: str, path: str):
        # проверить что текущая версия еще не зарегистрирована в agio
        # проверить что релиз с такой версией есть и там есть файлы whl
        # собрать полную информацию из __agio__.yml и pyproject.toml
        logger.debug(f"Register release in agio store: {path}")


class PackageCommandGroup(AGroupCommand):
    command_name = "pkg"
    commands = [PackageNewCommand, PackageBuildCommand, PackageReleaseCommand]
    help = 'Manage packages'
    # invoke_without_command = True

    # def execute(self, *args, **kwargs):
    #     print('Empty command executed: Package command')