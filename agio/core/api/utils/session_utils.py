import os
import json
from pathlib import Path

from agio.core.utils import config_dir

_session_file = 'session.json'


def _get_session_file() -> Path:
    return config_dir() / _session_file


def save_session(session):
    session_file = _get_session_file()
    session_file.parent.mkdir(exist_ok=True, parents=True)
    with session_file.open('w') as f:
        json.dump(session, f, indent=2)


def load_session():
    session_file = _get_session_file()
    if not session_file.exists():
        return None
    with session_file.open('r') as f:
        return json.load(f)


def clear_session():
    session_file = _get_session_file()
    if not session_file.exists():
        return None
    with session_file.open('w') as f:
        json.dump({}, f, indent=2)