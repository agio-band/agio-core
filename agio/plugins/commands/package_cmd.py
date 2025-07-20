from pathlib import Path

import click
import logging

from agio.core.entities import APackage, APackageRelease
from agio.core.pkg.package_repostory import APackageRepository
from agio.core.plugins.base_command import ACommandPlugin, ASubCommand

logger = logging.getLogger(__name__)


class PackageNewCommand(ASubCommand):
    command_name = "new"
    arguments = [
        click.option("-p", "--path", help='Package root path, Default: $PWD',
                     type=click.Path(exists=True, dir_okay=True, resolve_path=True),
                     default=Path.cwd().absolute().as_posix()),
    ]

    def execute(self, path: str):
        print(f"Create new package from {path}")
        pkg = APackageRepository(path).pkg_manager
        print('Package name:', pkg.package_name)
        new_pkg = APackage.create(pkg.package_name)
        print(f"New package created: {new_pkg.id}")


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
        APackageRepository(path).build(**kwargs)



class PackageReleaseCommand(ASubCommand):
    command_name = "release"
    arguments = [
        click.option('-t', '--token', envvar='AGIO_GIT_REPOSITORY_TOKEN',),
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
        repo =  APackageRepository(path)
        pkg_manager = repo.pkg_manager
        release_data = repo.make_release(**kwargs)
        release = APackageRelease.find(pkg_manager.package_name, release_data['version'])
        logger.info(f"Package release created: {release.id}")


class PackageCommand(ACommandPlugin):
    name = 'package_cmd'
    command_name = "pkg"
    subcommands = [
        PackageNewCommand,
        PackageBuildCommand,
        PackageReleaseCommand,
    ]
    help = 'Manage packages'
    arguments = [
        click.option('-i', '--info', is_flag=True, default=False, help='Show package information'),
    ]

    def execute(self, info, *args, **kwargs):
        if info:
            print('Show packages info... [TODO]')
        # else:
        #     click.echo("ERROR: Arguments not pass", err=True)
        #     self.context.exit(1)
