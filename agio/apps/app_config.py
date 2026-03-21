import json
from functools import cached_property
from threading import Lock
from typing import Any
from agio.tools.data_helpers import deep_tree
from agio.tools import local_dirs


class AppLocalConfig:
    _file_locker = Lock()

    def __init__(self, app_name: str, app_version: str = 'default'):
        self.app_name = app_name
        self.app_version = app_version
        self._data = None
        self.reload()

    @cached_property
    def local_config_file(self):
        save_dir = local_dirs.config_dir()
        return save_dir/'app-configs.json'

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def set(self, key: str, value: Any):
        self._data[key] = value

    def reload(self):
        if not self.local_config_file.exists():
            app_data = deep_tree()
        else:
            with open(self.local_config_file, 'r') as f:
                data = json.load(f)
            app_data = deep_tree(data.get(self.app_name, {}).get(self.app_version, {}))
        self._data = app_data

    def _load_full_config(self):
        if self.local_config_file.exists():
            with open(self.local_config_file, 'r') as f:
                all_data = deep_tree(json.load(f))
        else:
            all_data = deep_tree()
        return all_data

    def _save_full_config(self, data: dict):
        self.local_config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.local_config_file, 'w') as f:
            json.dump(dict(data), f, indent=2)

    def save(self):
        with self._file_locker:
            all_data = self._load_full_config()
            all_data[self.app_name][self.app_version] = self._data
            self._save_full_config(all_data)
