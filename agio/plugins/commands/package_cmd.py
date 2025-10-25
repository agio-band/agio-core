import logging
import re
from pathlib import Path

import click

from agio.core.entities import APackageRelease, AWorkspace
from agio.core.pkg.package_repostory import APackageRepository
from agio.core.plugins.base_command import ACommandPlugin, ASubCommand
from agio.core.utils.app_dirs import get_default_env_dir
from agio.core.utils.pkg_manager import get_package_manager
from agio.core.utils.text_utils import unslugify
from agio.tools import package_template

logger = logging.getLogger(__name__)


class PackageNewCommand(ASubCommand):
    command_name = "new"
    arguments = [
        click.argument("destination", type=click.Path(dir_okay=True, resolve_path=True),
                     default=Path.cwd().absolute().as_posix()),
        click.option("-n", "--name", help='Package name. Example: my-package',),
        click.option("-p", "--python-name", help='Python package name. Example: my_package. Default: slug from name',),
        click.option("-c", "--nice-name", help='Package name for docs. Example: My Package. Default: unslugify from name', required=False),
        click.option("-t", "--template", help='Use custom template', required=False, default=None),
        click.option("-q", "--quiet", help='Quiet creation', required=False, default=False, is_flag=True),

    ]

    def execute(self, destination: str, name: str = None, python_name: str = None,
                nice_name: str = None, template: str = None, quiet: bool = False):
        destination = Path(destination).expanduser().absolute()
        click.secho('Create new package', fg='green')
        try:
            name, python_name, nice_name = self.collect_data(name, python_name, nice_name)
        except KeyboardInterrupt:
            return
        click.secho('=== New Package Parameters: ===', fg='green')
        print('Name: ', end='')
        click.secho(name, fg='yellow')
        print('Py Package Name: ', end='')
        click.secho(python_name, fg='yellow')
        print('Nice Name: ', end='')
        click.secho(nice_name, fg='yellow')
        print('Destination path: ', end='')
        click.secho(destination, fg='yellow')
        click.secho('===============================', fg='green')
        if not quiet and not click.confirm('Do you want to continue?', default=True):
            print('Canceled')
        result = package_template.create_new_package(destination, name, python_name, nice_name)
        click.secho(f'Package Created: {result}', fg='green')

    def collect_data(self, name: str = None, python_name: str = None, nice_name: str = None):
        # project name
        while True:
            if not name:
                name = click.prompt("Package name")
            try:
                name = package_template.validate_package_name(name)
            except NameError as e:
                click.secho(f'Error: {e}', fg='red')
                name = ''
                continue
            break

        # python name
        if not python_name:
            try:
                default_py_name = package_template.validate_python_name(name)
            except NameError:
                default_py_name = None
            while True:
                python_name = click.prompt(f"Python package name", default=default_py_name)
                try:
                    python_name = package_template.validate_python_name(python_name)
                except NameError as e:
                    click.secho(f"Error: {e} ", fg='red')
                    continue
                break
        else:
            python_name = package_template.validate_python_name(name)
        # docs name
        if not nice_name:
            default_nice_name = unslugify(name)
            # agio to lowercase :)
            default_nice_name = re.sub(r'agio', 'agio', default_nice_name, flags=re.IGNORECASE)
            nice_name = click.prompt(f"Package name for docs", default=default_nice_name)
        return name, python_name, nice_name


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


class PackageRegisterCommand(ASubCommand):
    command_name = "register"
    arguments = [
        click.argument("path",
                        type=click.Path(exists=True, dir_okay=True, resolve_path=True),
                        default=Path.cwd().absolute().as_posix(),
                        metavar='[PACKAGE_PATH]'
                       ),
    ]

    def execute(self, path: str|Path, **kwargs):
        """
        PATH: path to package repository
        """
        logger.info(f"Register package {path}...")
        pkg = APackageRepository(path).register_package(**kwargs)
        logger.info(f"Package registered: {pkg}")


class PackageReleaseCommand(ASubCommand):
    command_name = "release"
    arguments = [
        click.option('-t', '--token', envvar='AGIO_GIT_REPOSITORY_TOKEN',),
        click.option('-b', '--no-check-branch', is_flag=True, default=False, help='Skip branch check'),
        click.option('-c', '--no-check-commits', is_flag=True, default=False, help='Skip commits check'),
        click.option('-p', '--no-check-pushed', is_flag=True, default=False, help='Skip push check'),
        click.option('-l', '--no-cleanup', is_flag=True, default=False, help='Skip cleanup build files'),
        click.option('-r', '--replace', is_flag=True, default=False, help='Replace existing release'),
        click.argument("path",
                     type=click.Path(exists=True, dir_okay=True, resolve_path=True),
                     default=Path.cwd().absolute().as_posix()),
    ]

    def execute(self, token: str, path: str, **kwargs):
        logger.debug(f"Make package release: {path}")
        repo =  APackageRepository(path)
        pkg_manager = repo.pkg_manager
        release_data = repo.make_release(token=token, **kwargs)
        release = APackageRelease.find(pkg_manager.package_name, release_data['version'])
        logger.info(f"Package release created: {release.id}")


class PackageInfoCommand(ASubCommand):
    command_name = "info"
    arguments = [
        click.option('-i', '--info', is_flag=True, default=False, help='Show package information'),
    ]

    def execute(self, **kwargs):
        click.secho('Show packages info... [TODO]', fg='yellow')


class PackageInstallCommand(ASubCommand):
    command_name = "install"
    arguments = [
        click.argument("name",),
        click.option('-v', '--version', default=None, help='Package version to install'),
    ]

    def execute(self, name: str, version: str):
        click.secho(f'Install package "{name}"' + f' v{version}' if version else '', fg='green')
        try:
            ws_manager = AWorkspace.current()
            manager = ws_manager.get_manager().venv_manager
        except RuntimeError:
            manager = get_package_manager(get_default_env_dir())
        try:
            resp = manager.install_package_by_name(name, version)
            print(resp)
        except Exception as e:
            click.secho(f'Install package "{name}" failed: {e}', fg='red')


class PackageUninstallCommand(ASubCommand):
    command_name = "uninstall"
    arguments = [
        click.argument("name",),
    ]

    def execute(self, name: str, **kwargs):
        click.secho(f'Uninstall package "{name}"', fg='red')
        try:
            ws_manager = AWorkspace.current()
            manager = ws_manager.get_manager().venv_manager
        except RuntimeError:
            manager = get_package_manager(get_default_env_dir())
        try:
            resp = manager.uninstall_package(name)
            print(resp)
        except Exception as e:
            click.secho(f'Install package "{name}" failed: {e}', fg='red')



class PackageCommand(ACommandPlugin):
    name = 'package_cmd'
    command_name = "pkg"
    subcommands = [
        PackageNewCommand,
        PackageBuildCommand,
        PackageReleaseCommand,
        PackageRegisterCommand,
        PackageInfoCommand,
        PackageInstallCommand,
        PackageUninstallCommand,
    ]
    help = 'Manage packages'
