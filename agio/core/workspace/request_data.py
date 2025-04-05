from pathlib import Path

import requests

api_url = 'http://0.0.0.0:8002'

# workspaces
ws_api_url = f'{api_url}/workspace'

def list_workspaces():
    return requests.get(api_url).json()


def create_workspace(name: str, packages: list):
    pass


def get_workspace_data(workspace_id: str):
    return requests.get(f'{ws_api_url}/{workspace_id}').json()


def update_workspace(workspace_id: str, data: dict):
    return requests.patch(f'{ws_api_url}/{workspace_id}', json=data).json()


def delete_workspace(workspace_id: str):
    return requests.delete(f'{ws_api_url}/{workspace_id}').json()


def get_workspaces_installation_root():
    return Path('~/.agio/workspaces').expanduser()

# packages
pkg_api_url = f'{api_url}/package'

def list_packages():
    return requests.get(f'{pkg_api_url}').json()


def get_package(name: str, version: str):
    resp = requests.get(f'{pkg_api_url}/{name}/{version}')
    resp.raise_for_status()
    return resp.json()

def get_packages():
    resp = requests.get(f'{pkg_api_url}')
    resp.raise_for_status()
    return resp.json()