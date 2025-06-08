import json
from pathlib import Path

from agio.core.main import package_hub
from agio.core.settings import LocalSettingsHub
from agio.core.packages.package import APackage

settings_root = Path('~/.agio/settings').expanduser()

def collect_local_settings():
    # get all packages list and collect settings classes for local settings
    # pkg_settings_list = {}
    # for name, package in package_hub.get_packages().items():  #type: APackage
    #     cls = package.get_local_settings_class()
    #     if cls:
    #         pkg_settings_list[name] = cls
    # merge models
    # print(pkg_settings_list)
    # read settings from files
    settings = read_local_settings_values()
    # apply values
    settings_hub = LocalSettingsHub(settings)
    return settings_hub


def collect_workspace_settings():
    # create workspace instance
    # get workspace settings from server
    # iterate over packages
    #   create package settings instance
    # create workspace settings instance with applied values
    pass


def read_local_settings_values():

    path_list = [
        settings_root/'common_settings.json'
    ]
    # TODO: for project
    # TODO: for studio
    # read data
    settings_data = {}
    for path in path_list:
        if path.exists():
            with path.open(encoding='utf-8') as f:
                data = json.load(f)
            settings_data.update(data)
    return settings_data


def write_common_settings(data: dict):
    save_path = settings_root / 'common_settings.json'
    with save_path.open('w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)