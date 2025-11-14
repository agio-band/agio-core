import hashlib
import json
import logging
import os
import shutil
import time
from functools import cache
from pathlib import Path

from agio.core.config import config
from agio.core.exceptions import AuthorizationError
from agio.tools import app_dirs, process_utils, thread_tools


logger = logging.getLogger(__name__)

def get_token(platform_url: str = None, client_id: str = None,
              auth_local_port: int = None, token_only: bool = False,
              cache_dir: str = None, refresh_only: bool = False) -> str|dict:

    timeout = 2 if refresh_only else 180
    locker = thread_tools.locker('agio-login', expire=timeout)
    if locker.locked():
        # wait if locked ???
        time.sleep(2.5)
        if locker.locked():
            raise AuthorizationError('Authorization processing is already in progress')

    platform_url = platform_url or config.API.PLATFORM_URL.rstrip('/')

    client_id = client_id or config.API.CLIENT_ID
    auth_local_port = auth_local_port or config.API.AUTH_LOCAL_PORT
    cache_dir = cache_dir or _get_session_cache_dir()
    agio_login_binary = _get_agio_login_binary()

    cmd = [
        agio_login_binary,
        'get-token',
        '--oidc-issuer-url', f'{platform_url}/.ory/hydra/public',
        '--oidc-client-id', client_id or config.API.CLIENT_ID,
        '--listen-address', f'localhost:{auth_local_port}',
        '--oidc-extra-scope', 'offline',
        '--authentication-timeout-sec', str(timeout)
    ]
    if cache_dir:
        cmd += ['--token-cache-dir', cache_dir]
    if refresh_only:
        cmd += ['--skip-open-browser']

    with locker:
        logger.debug(' '.join(cmd))
        resp = process_utils.start_process(cmd, get_output=True, new_console=False, timeout=timeout)
    if not resp:
        raise AuthorizationError
    token_data = json.loads(resp)
    if token_only:
        return token_data['AccessToken']
    else:
        return token_data


def logout(base_url=None):
    cache_file = _cache_file_path(base_url)
    if cache_file.exists():
        cache_file.unlink()
    cache_dir = Path(_get_session_cache_dir())
    if cache_dir.exists():
        shutil.rmtree(cache_dir)
    logger.debug('Logged out')


def _get_session_cache_dir():
    # default cache dir for agio.drive
    if os.name == 'nt':
        return os.path.expandvars(r'%APPDATA%\Roaming\agio\cache\oidc-login')
    else:
        return os.path.expanduser('~/.config/agio/cache/oidc-login')


def _cache_file_path(base_url=None):
    platform_url = base_url or config.API.PLATFORM_URL.rstrip('/')
    key = hashlib.md5(platform_url.encode('utf-8')).hexdigest()
    cache_file = app_dirs.cache_dir(f'session-{key}.json')
    return cache_file


def read_auth_cache_file(base_url=None):
    cache_file = _cache_file_path(base_url)
    if cache_file.exists():
        with open(cache_file, ) as f:
            cache_data = json.load(f)
        return cache_data
    return {}


def write_cache_file(cache_data, base_url=None):
    cache_file = _cache_file_path(base_url)
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    with open(cache_file, mode='w') as f:
        json.dump(cache_data, f, indent=2)


def _get_agio_login_binary() -> str:
    # overridden
    if config.API.LOGIN_BINARY:
        if not Path(config.API.LOGIN_BINARY).exists():
            raise FileNotFoundError(f'File {config.API.LOGIN_BINARY} does not exist')
        return config.API.LOGIN_BINARY
    # downloaded
    path = next(app_dirs.binary_files_dir().glob('agio-login*'), None)
    if path:
        return str(path)
    # global
    path = shutil.which('agio-login')
    if path:
        return path
    raise FileNotFoundError('agio-login binary not found')
