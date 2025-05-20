from pathlib import Path

import click
import logging
from agio.core.plugins.base.base_plugin_command import ACommandPlugin, ASubCommand
from agio.core.packages import package_tools

logger = logging.getLogger(__name__)


class PackageNewCommand(ASubCommand):
    command_name = "new"
    arguments = [
        click.option("-p", "--path", help='Package root path, Default: $PWD',
                     type=click.Path(exists=True, dir_okay=True, resolve_path=True),
                     default=Path.cwd().absolute().as_posix()),
    ]

    def execute(self, path: str):
        print(f"Create new package in {path}")


class PackageBuildCommand(ASubCommand):
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
        # --no-cache
        # --cache-dir <CACHE_DIR>
        logger.info(f"Build package {path}")
        package_tools.build_package(path, **kwargs)


class PackageReleaseCommand(ASubCommand):
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
        logger.info(f"Release created: ID {result['id']}")


class PackageRegisterCommand(ASubCommand):
    command_name = "register"
    arguments = [
        click.argument("path",
                     type=click.Path(exists=True, dir_okay=True, resolve_path=True),
                     default=Path.cwd().absolute().as_posix()),
    ]

    def execute(self, path: str):
        logger.debug(f"Register release in agio store: {path}")
        resp = package_tools.register_package(path)
        print(resp)


class PackageCommand(ACommandPlugin):
    name = 'package_command'
    command_name = "pkg"
    subcommands = [PackageNewCommand, PackageBuildCommand, PackageReleaseCommand, PackageRegisterCommand]
    help = 'Manage packages'
    arguments = [
        click.option('-i', '--info', is_flag=True, default=False, help='Show package information'),
    ]

    def execute(self, info, *args, **kwargs):
        if info:
            print('Show packages info... [TODO]')
        else:
            click.echo("ERROR: Arguments not pass", err=True)
            self.context.exit(1)
