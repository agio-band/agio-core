import os
import json


_session_file = 'session.json'


def _get_user_config_dir():
    if os.name == 'nt':
        return os.getenv('APPDATA')
    elif os.name == 'posix':
        if 'XDG_CONFIG_HOME' in os.environ:
            return os.environ['XDG_CONFIG_HOME']
        else:
            return os.path.join(os.path.expanduser('~'), '.config')
    elif os.name == 'mac':
        return os.path.join(os.path.expanduser('~'), 'Library', 'Application Support')
    else:
        raise OSError("Unsupported operating system")


def get_agio_config_dir():
    agio_dir = os.path.join(_get_user_config_dir(), 'agio')
    os.makedirs(agio_dir, exist_ok=True)
    return agio_dir


def _get_session_file():
    return os.path.join(get_agio_config_dir(), _session_file)


def save_session(session):
    with open(_get_session_file(), 'w') as f:
        json.dump(session, f, indent=2)


def load_session():
    session_file = _get_session_file()
    if not os.path.exists(session_file):
        return None
    with open(session_file, 'r') as f:
        return json.load(f)
