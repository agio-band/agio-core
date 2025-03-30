import os
from email.policy import default
from pathlib import Path

import click
from soupsieve.css_types import pickle_register

from agio.core.plugins.plugin_cmd_base import ACommand, SubCommand
# from agio.core.packages.package_base import APackage


# class NewPackageCommand(SubCommand):
#     command_name = 'new'
#     arguments = [
#         click.argument('package_name'),
#         click.option('-w', '--workdir', )
#     ]
#
#     def execute(self, package_name: str, workdir: str = None):
#         print('Create new package', package_name, 'in', workdir)
#         # APackage.create_new_package(package_name, workdir)
#
#
# class PackageCommand(ACommand):
#     command_name = 'package'
#     arguments = [
#         # click.option("-d", "--workdir", help='Root Dir'),
#         # click.argument('command')#, help='Supported commands: build, cbuild'),
#     ]
#     subcommands = [
#         NewPackageCommand
#     ]
#
#     def execute(self, workdir: str = None):
#         print('Set workdir', workdir)

    # def execute(self, command: str, workdir: str = None):
    #     match command:
    #         case 'build':
    #             self.build_package(workdir)
    #         case 'cbuild':
    #             self.cbuild_package(workdir)
    #         case _:
    #             raise Exception(f'Unknown command {command}')

    #
    # def build_package(self, path: str = None):
    #     if not path:
    #         path = os.getcwd()
    #     print('Build package in', path, 'using uv')
    #     # ub build
    #
    # def cbuild_package(self, path):
    #     if not path:
    #         path = os.getcwd()
    #     print('Build package in', path, 'using cibuildwheel')
    #     # cibuildwheel --output-dir dist


    # def verify_is_agio_package(self, path: str):
    #     pass




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