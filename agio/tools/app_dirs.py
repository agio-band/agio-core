import json
import logging
import os
import sys
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)

IS_WINDOWS = sys.platform == 'win32'
IS_LINUX = sys.platform == 'linux'
IS_MAC = sys.platform == 'darwin'


def install_dir() -> Path:
    """Path where agio software is installed"""
    from_env = os.getenv("AGIO_INSTALL_PATH")
    if from_env:
        return Path(from_env)
    return get_global_config().get('install_path') or default_install_dir()


def default_install_dir(*inner_parts) -> Path:
    if IS_LINUX:
        return Path('~/.local/share/agio', *inner_parts).expanduser()
    elif IS_WINDOWS:
        return Path(os.path.expandvars(r'%LOCALAPPDATA%\agio'), *inner_parts)
    elif IS_MAC:
        return Path('~/Applications/agio', *inner_parts).expanduser()


def config_dir(*inner_parts: str) -> Path:
    """Path where agio configs is stored"""
    if IS_LINUX:
        return Path('~/.config/agio', *inner_parts).expanduser()
    elif IS_WINDOWS:
        return Path(os.path.expandvars(r'%APPDATA%\agio'), *inner_parts)
    elif IS_MAC:
        return Path('~/Library/Preferences/agio', *inner_parts)


def projects_settings_dir(*inner_parts: str) -> Path:
    return config_dir('projects', *inner_parts)


def cache_dir(*inner_parts) -> Path:
    """Path for cache data"""
    # install_dir('cache') ???
    if IS_LINUX:
        return Path('~/.cache/agio', *inner_parts).expanduser()
    elif IS_WINDOWS:
        return Path(os.path.expandvars(r'%LOCALAPPDATA%\cache\agio'), *inner_parts)
    elif IS_MAC:
        return Path('~/Library/Caches/agio', *inner_parts).expanduser()


def binary_files_dir(*inner_parts) -> Path:
    """Executable standalone files and libraries"""
    return install_dir('bin', *inner_parts)


def user_binary_path_dir() -> Path:
    """Path for binary files or symlinks, added to PATH env by default"""
    if IS_LINUX:
        return Path('~/.local/bin').expanduser()
    elif IS_WINDOWS:
        return Path(os.path.expandvars(r'%LOCALAPPDATA%\Microsoft\WindowsApps'))
    elif IS_MAC:
        # TODO: need to add to ~/.zshrc or ~/.bashrc
        return Path('~/.local/bin').expanduser()


def temp_dir(*inner_parts) -> Path:
    """
    path for temporary files
    also you can use tempfile.TemporaryDirectory
    """
    path = Path(tempfile.gettempdir(), 'agio', *inner_parts)
    path.mkdir(parents=True, exist_ok=True)
    return path


# venv directories
def venv_installation_root(install_path: str|Path = None) -> Path:
    """All virtual envs root"""
    if install_path is None:
        conf = get_global_config()
        install_path = conf.get('install_path')
    if install_path:
        return Path(install_path, 'venvs')
    else:
        return Path(install_dir(), 'venvs')


def default_env_install_dir(install_path: str | Path = None) -> Path:
    """Default virtualenv for global standalone app"""
    return  Path(venv_installation_root(install_path), 'default')


def workspaces_install_dir(install_path: str | Path = None) -> Path:
    """Store path for projects and dcc venvs"""
    return Path(venv_installation_root(install_path), 'workspaces')


# config file
def get_global_config_file_path() -> Path:
    return config_dir('user-config.json')


def get_global_config() -> dict:
    """
    install_path: str
    add_desktop_shortcut: bool
    add_main_menu_shortcut: bool
    """
    config_file = get_global_config_file_path()
    if not config_file.exists():
        return {}
    try:
        with open(config_file, 'r') as f:
            data = json.load(f)
    except Exception as e:
        logger.error('Failed read info file', e)
        return {}
    return data


def save_global_config(data: dict):
    allowed_keys = ('install_path', 'add_desktop_shortcut', 'add_main_menu_shortcut')
    data = {k: v for k, v in data.items() if k in allowed_keys}
    config_file = get_global_config_file_path()
    config_file.parent.mkdir(parents=True, exist_ok=True)
    with open(config_file, 'w') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def delete_global_config_file():
    file = get_global_config_file_path()
    if file.exists():
        file.unlink()
