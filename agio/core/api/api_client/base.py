import base64
import logging
import threading
import time
# from http.server import HTTPServer, BaseHTTPRequestHandler
# from pathlib import Path
# from urllib.parse import urlparse, parse_qs
# import webbrowser

import requests
from requests_oauthlib import OAuth2Session

from agio.core.api.api_client.auth_server import run_oauth_server
from agio.core import events
from agio.core.utils import config
from agio.core.api.utils import session_utils
from agio.core.exceptions import AuthorizationError

logger = logging.getLogger(__name__)


class _ApiClientAuth:
    platform_url = config.API.PLATFORM_URL
    base_api_url = f'{platform_url}/graphql'
    authorization_base_url = f'{config.API.PLATFORM_URL}/.ory/hydra/public/oauth2/auth'
    token_url = f'{config.API.PLATFORM_URL}/.ory/hydra/public/oauth2/token'
    redirect_uri = f'http://localhost:{config.API.AUTH_LOCAL_PORT}/oauth_callback'
    scope = ['openid', 'offline']
    default_client_id = config.API.DEFAULT_CLIENT_ID

    def __init__(self, *args, **kwargs):
        self._expire_time = None
        self.session = requests.Session()
        self._restore_session(token=kwargs.get('session_token'))

    def login(self, client_id: str = None):
        client_id = client_id or self.default_client_id
        # long time blocking command !
        token = self._do_login(client_id)
        if token:
            self._set_token(token)
            logger.info('Logged in')
            self._save_session(token, client_id)
        else:
            raise AuthorizationError

    def logout(self):
        self.session.headers.pop('Authorization', None)
        self._clear_session()
        logger.info('Logged out')

    def _do_login(self, client_id: str) -> dict|None:
        stop_event = threading.Event()

        token, thread = run_oauth_server(
            client_id=client_id or config.API.DEFAULT_CLIENT_ID,
            scope=['openid', 'offline'],
            authorization_base_url=f'{config.API.PLATFORM_URL}/.ory/hydra/public/oauth2/auth',
            token_url=f'{config.API.PLATFORM_URL}/.ory/hydra/public/oauth2/token',
            port=config.API.AUTH_LOCAL_PORT,
            stop_event=stop_event
        )
        is_canceled = False
        def cancel(*args, **kwargs):
            nonlocal is_canceled
            stop_event.set()
            is_canceled = True

        with events.subscribe_manager('core.app.exit', cancel):
            thread.join()
        if is_canceled:
            return None
        return token or None

    def _refresh_token(self):
        logging.debug('Refresh token...')
        session = self._load_session()
        oauth = OAuth2Session(client_id=session['client_id'], scope=self.scope)
        encoded_client_id = base64.encodebytes((session['client_id'] + ':').encode()).decode().strip()
        headers = {'Authorization': f"Basic {encoded_client_id}", 'Content-Type': 'application/x-www-form-urlencoded'}
        new_session = oauth.refresh_token(self.token_url, refresh_token=session['refresh_token'], headers=headers)
        self._save_session(new_session, client_id=session.get('client_id'))
        self._set_token(new_session)

    def _set_token(self, session: dict):
        self.session.headers.update({
            'Authorization': f'Bearer {session["access_token"]}',
            "Content-Type": "application/json",
        })
        self._expire_time = int(session.get('expires_at', 0))

    def _save_session(self, token: dict, client_id: str = None):
        if client_id:
            token['client_id'] = client_id
        session_utils.save_session(token)

    def _load_session(self):
        return session_utils.load_session()

    def _restore_session(self, token: str = None):
        if token:
            self._set_token({'access_token': token})
        else:
            session = self._load_session()
            if session:
                self._set_token(session)

    def _clear_session(self):
        session_utils.clear_session()

    def check_is_expire(self):
        """
        Refresh token if expire time is less than current time
        """
        if self._expire_time and (self._expire_time - 100) < int(time.time()):     # offset -100 sec
            self._refresh_token()


class RestApiClientBase(_ApiClientAuth):
    """Not used now"""
    _base_api_url = None

    def __getattribute__(self, name):
        if name in ('get', 'post', 'put', 'patch', 'delete'):
            self.check_is_expire()
        return super().__getattribute__(name)

    def get(self, *args, **kwargs):
        raise NotImplementedError

    def post(self, *args, **kwargs):
        raise NotImplementedError

    def put(self, *args, **kwargs):
        raise NotImplementedError

    def patch(self, *args, **kwargs):
        raise NotImplementedError

    def delete(self, *args, **kwargs):
        raise NotImplementedError


