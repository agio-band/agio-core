from pathlib import Path

import requests


api_url = 'http://0.0.0.0:8002/workspace'

def list_workspaces():
    return requests.get(api_url).json()


def create_workspace(name: str, packages: list):
    pass


def load_workspace_data(workspace_id: str):
    return requests.get(f'{api_url}/{workspace_id}').json()


def update_workspace(workspace_id: str, data: dict):
    return requests.patch(f'{api_url}/{workspace_id}', json=data).json()


def delete_workspace(workspace_id: str):
    return requests.delete(f'{api_url}/{workspace_id}').json()


def get_workspaces_installation_root():
    return Path('~/.agio/workspaces').expanduser()

def get_package_manager():
    return 'pip'