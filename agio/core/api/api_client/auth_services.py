import json
import os
import shutil
from functools import cache
from pathlib import Path

from agio.core import config
from agio.core.exceptions import AuthorizationError
from agio.tools import app_dirs, process_utils


def get_token(platform_url: str = None, client_id: str = None,
              auth_local_port: int = None, token_only: bool = False,
              cache_dir: str = None) -> str|dict:
    platform_url = platform_url or config.API.PLATFORM_URL.rstrip('/')
    client_id = client_id or config.API.DEFAULT_CLIENT_ID
    auth_local_port = auth_local_port or config.API.AUTH_LOCAL_PORT
    cache_dir = cache_dir or _get_session_cache_dir()
    agio_login_binary = _get_agio_login_binary()
    cmd = [
        agio_login_binary,
        'get-token',
        '--oidc-issuer-url', f'{platform_url}/.ory/hydra/public',
        '--oidc-client-id', client_id or config.API.DEFAULT_CLIENT_ID,
        '--listen-address', f'localhost:{auth_local_port}',
        '--oidc-extra-scope', 'offline'
    ]
    if cache_dir:
        cmd += ['--token-cache-dir', cache_dir]
    resp = process_utils.start_process(cmd, get_output=True, new_console=False)
    if not resp:
        raise AuthorizationError
    token_data = json.loads(resp)
    if token_only:
        return token_data['AccessToken']
    else:
        return token_data


def logout():
    cache_dir = Path(_get_session_cache_dir())
    if cache_dir.exists():
        shutil.rmtree(cache_dir)
        return True
    return False


def _get_session_cache_dir():
    # default cache dor for agio.drive
    if os.name == 'nt':
        return os.path.expandvars(r'%APPDATA%\Roaming\agio\cache\oidc-login')
    else:
        return os.path.expanduser('~/.config/agio/cache/oidc-login')


@cache
def _get_agio_login_binary() -> str:
    path = shutil.which('agio-login')
    if path:
        return path
    path = next(app_dirs.binary_files_dir().glob('agio-login*'), None)
    if path:
        return str(path)
    path = os.getenv('AGIO_LOGIN_BINARY')
    if path:
        if not Path(path).exists():
            raise FileNotFoundError(f'File {path} does not exist')
        return path
    raise FileNotFoundError('agio-login binary not found')
