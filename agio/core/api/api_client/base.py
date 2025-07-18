import base64
import logging
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse, parse_qs
import webbrowser

import requests
from requests_oauthlib import OAuth2Session

from agio.core.utils import config
from agio.core.api.utils import session_utils
from agio.core.exceptions import AuthorizationError

logger = logging.getLogger(__name__)


def _get_template_content(name):
    page_file_path = Path(__file__).parent.parent / f'templates/{name}.html'
    if not page_file_path.exists():
        raise FileNotFoundError(f"File {page_file_path} not found")
    return page_file_path.read_text()

def _success_page_text():
    return _get_template_content('success_page')


def _error_page_text():
    return _get_template_content('error_page')




class _ApiClientAuth:
    platform_url = config.API.PLATFORM_URL
    authorization_base_url = f'{config.API.PLATFORM_URL}/.ory/hydra/public/oauth2/auth'
    token_url = f'{config.API.PLATFORM_URL}/.ory/hydra/public/oauth2/token'
    redirect_uri = f'http://localhost:{config.API.AUTH_LOCAL_PORT}/oauth_callback'
    scope = ['openid', 'offline']
    default_client_id = config.API.DEFAULT_CLIENT_ID

    def __init__(self, *args, **kwargs):
        self._expire_time = None
        self.session = requests.Session()
        self._restore_session()

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
        logger.info('Logged out')
        return self.session.headers.get('Authorization') is None

    def is_logged_in(self):
        return self.session.headers.get('Authorization') is not None

    def _do_login(self, client_id: str) -> dict:
        """
        Web browser will be opened
        """
        logging.debug(f'Login... {self.authorization_base_url} with client_id={client_id}')
        oauth = OAuth2Session(client_id, scope=self.scope, redirect_uri=self.redirect_uri)
        authorization_url, state = oauth.authorization_url(self.authorization_base_url)
        token = dict()

        class RequestHandler(BaseHTTPRequestHandler):

            def do_GET(self):
                nonlocal token
                if self.path.startswith('/oauth_callback'):
                    parsed_url = urlparse(self.path)
                    code = parse_qs(parsed_url.query).get('code')
                    if code:
                        code = code[0]
                        token = oauth.fetch_token(_ApiClientAuth.token_url, client_secret='', code=code)
                        self.send_response(200)
                        self.send_header('Content-type', 'text/html')
                        self.end_headers()
                        self.wfile.write(_success_page_text().encode())
                    else:
                        self.send_response(400)
                        self.send_header('Content-type', 'text/html')
                        self.end_headers()
                        self.wfile.write(_error_page_text().encode())
                else:
                    self.send_response(302)
                    self.send_header('Location', authorization_url)
                    self.end_headers()

        httpd = HTTPServer(('localhost', config.API.AUTH_LOCAL_PORT), RequestHandler)     # type: ignore
        logging.info(f'Auth URL: {authorization_url}')
        webbrowser.open(authorization_url)
        httpd.handle_request()
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

    def _restore_session(self):
        session = self._load_session()
        if session:
            self._set_token(session)

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


