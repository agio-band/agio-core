import json
from pathlib import Path
from agio.core.settings import LocalSettingsHub, WorkspaceSettingsHub


settings_root = Path('~/.agio/settings').expanduser()


def collect_local_settings() -> LocalSettingsHub:
    # read local settings from files
    settings = read_local_settings_values()
    # create local settings instance with applied values
    return LocalSettingsHub(settings)


def collect_workspace_settings() -> WorkspaceSettingsHub|None:
    from agio.core.workspace.workspace import AWorkspace
    # create workspace instance
    ws = AWorkspace.current()
    if not ws:
        return
    # get workspace settings from server
    settings = {}
    # create workspace settings instance with applied values
    return WorkspaceSettingsHub(settings)


def read_local_settings_values():
    path_list = [
        settings_root/'common_settings.json'
    ]
    # TODO: add project overrides
    # TODO: add studio overrides
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


# layout

def collect_local_settings_layout() -> dict:
    pass

def collect_workspace_settings_layout() -> dict:
    pass