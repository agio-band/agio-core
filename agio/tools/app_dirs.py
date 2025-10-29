import os
import sys
import tempfile
from pathlib import Path

IS_WINDOWS = sys.platform == 'win32'
IS_LINUX = sys.platform == 'linux'
IS_MAC = sys.platform == 'darwin'


def install_dir(*inner_parts) -> Path:
    """Path where agio software is installed"""
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

def pyenv_installation_root(*args) -> Path:
    """All virtual envs"""
    return cache_dir('pyenv', *args)


def default_env_dir() -> Path:
    """Default virtualenv for standalone app"""
    from_env = os.getenv("AGIO_DEFAULT_ENV_PATH")
    return from_env or pyenv_installation_root('default-env')


def workspaces_install_root() -> Path:
    """All custom envs for projects and dcc"""
    return pyenv_installation_root('workspaces')