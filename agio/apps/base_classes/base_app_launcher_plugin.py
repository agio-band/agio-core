from __future__ import annotations

from pathlib import Path

from agio.core.plugins.base_plugin import APlugin
from agio_apps.utils import app_launcher as bapp
from agio_apps.exceptions import ApplicationError


class ApplicationLauncherPlugin(APlugin):
    plugin_type = 'app_launcher'
    app_group: str = None
    app_name: str = None # required
    app_mode: str = None # required
    app_mode_label: str = None # required
    icon: str = None
    label: str = None
    bin_path: str = None
    required_attrs = {'app_name', 'app_group', 'app_mode', 'bin_path'}
    __is_base_plugin__ = True

    def __str__(self):
        return f"{self.app_name}/{self.app_mode}"

    def __repr__(self):
        return f"<{self.__class__.__name__} {self}>"

    def get_label(self):
        return self.label or self.app_name.title()

    def get_launch_args(self, app: bapp.AApplicationLauncher, config_args: list = None) -> tuple|list|None:
        """
        Extend or modify args
        """
        return config_args

    def get_launch_envs(self, app: bapp.AApplicationLauncher, envs: dict = None):
        """Create custom envs"""
        return {}

    def get_user_prefs_dir(self, app: bapp.AApplicationLauncher):
        pass

    def get_bin_basename(self, app: bapp.AApplicationLauncher):
        if not self.bin_path:
            raise ApplicationError('Bin file name not set')
        bin_file_name = self.bin_path.format(version=app.version)
        return bin_file_name

    def get_executable(self, app: bapp.AApplicationLauncher) -> str:
        bin_file_name = self.get_bin_basename(app)
        return Path(app.get_install_dir(), bin_file_name).as_posix()

    def get_workdir(self, app: bapp.AApplicationLauncher) -> str:
        """
        Modify workdir for current mode
        """
        return app.get_install_dir()

    def on_before_startup(self, app: bapp.AApplicationLauncher) -> None:
        pass

    def on_after_startup(self, app: bapp.AApplicationLauncher) -> None:
        pass

    def on_after_shutdown(self, app: bapp.AApplicationLauncher) -> None:
        pass


