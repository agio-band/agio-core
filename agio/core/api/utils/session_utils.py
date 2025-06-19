import os
import json

from agio.core import config, get_agio_config_dir

_session_file = 'agio_session.json'


def _get_session_file():
    store_dir = config.api.SESSION_STORE_DIR or get_agio_config_dir()
    return os.path.join(store_dir, _session_file)


def save_session(session):
    with open(_get_session_file(), 'w') as f:
        json.dump(session, f, indent=2)


def load_session():
    session_file = _get_session_file()
    if not os.path.exists(session_file):
        return None
    with open(session_file, 'r') as f:
        return json.load(f)
