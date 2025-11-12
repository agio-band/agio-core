import json
import logging
import os
from pathlib import Path

import requests
from requests.exceptions import HTTPError, ConnectionError, JSONDecodeError
from agio.core.config import config
from agio.core.api.api_client import auth_services
from agio.core.api.utils import NOTSET
from agio.tools import env_names
from agio.core.exceptions import RequestError, AuthorizationError
from agio.tools.json_serializer import JsonSerializer
from agio.core.events import emit

logger = logging.getLogger(__name__)


class ApiClient:
    platform_url = config.API.PLATFORM_URL.rstrip('/')
    base_api_url = f'{platform_url}/graphql'
    queries_root = Path(__file__).parent.parent.joinpath('queries')

    def __init__(self, *args, **kwargs):
        self.session = requests.Session()
        self._debug_query = bool(os.getenv(env_names.DEBUG_QUERY))

    def login(self):
        # long time blocking command !
        token = auth_services.get_token()
        if token:
            self._set_token(token)
            logger.info('Logged in')
            emit('core.auth.user_logged_in')
        else:
            raise AuthorizationError

    def logout(self):
        self.session.headers.pop('Authorization', None)
        auth_services.logout()
        logger.info('Logged out')
        emit('core.auth.user_logged_out')

    def _set_token(self, session: dict):
        self.session.headers.update({
            'Authorization': f'Bearer {session["AccessToken"]}',
            "Content-Type": "application/json",
        })

    def set_debug_query(self, val: bool):
        self._debug_query = bool(val)

    def _serialize_values(self, value: dict):
        # TODO optimise it
        return json.loads(json.dumps(value, cls=JsonSerializer))

    def ping(self):
        try:
            requests.get(self.platform_url).raise_for_status()
            return True
        except (HTTPError, ConnectionError):
            return False

    def make_query(self, query_file: str, **variables) -> dict:
        """Read query from file and execute query"""
        query_text = self.load_query(query_file)
        return self.make_query_raw(query_text, **variables)

    def make_query_raw(self, query: str, **variables) -> dict:
        """Execute query from string"""
        variables = self._remove_notset_values(variables)
        serialized = self._serialize_values(variables)
        data = {
            "query": query,
        }
        if serialized:
            data.update({
                "variables": serialized,
            })
        if self._debug_query:
            emit('core.api.debug_query_request_data', {'data': data})
            self._pprint_request(data)
        result = self._do_request(data)
        if self._debug_query:
            emit('core.api.debug_query_response_data', {'data': result})
            self._print_response(result)
        return result

    def load_query(self, query_path: str) -> str:
        """
        Load GraphQL query from file
        """
        query_file_path = self.queries_root.joinpath(query_path).with_suffix('.graphql')
        if not query_file_path.exists():
            raise FileNotFoundError(f'Query file not found: {query_path}')
        return query_file_path.read_text(encoding='utf-8')

    def _do_request(self, data, attempt: int = 0):
        response = self.session.post(self.base_api_url, json=data)
        if not response.ok:
            logger.error(f"Request failed with status code: {response.status_code}")

        try:
            response.raise_for_status()
        except HTTPError as e:
            try:
                resp_data = response.json()
                resp_data = resp_data['error']['status']
            except JSONDecodeError:
                resp_data = response.text
            raise RequestError(f'{resp_data}') from e

        result = response.json()

        if self._is_unauthorized_error(result):
            if attempt >= config.API.MAX_LOGIN_ATTEMPTS:
                emit('core.api.unauthorized_error', {'attempts': attempt})
                raise AuthorizationError('You are not authorized')
            self.login()
            return self._do_request(data, attempt=attempt + 1)
        self._check_response_errors(result)
        return result

    def _is_unauthorized_error(self, response: dict) -> bool:
        if 'errors' in response:
            for error in response['errors']:
                if error['message'] == 'UNAUTHORIZED':
                    return True

    def _check_response_errors(self, response: dict):
        if 'errors' in response:
            raise RequestError('\n'.join(x['message'] for x in response['errors']))

    def _pprint_request(self, data):
        print('< QUERY >'.center(50, '='))
        print(data['query'])
        print('< VARIABLES >'.center(50, '='))
        print(json.dumps(data.get('variables'), indent=2).replace('\\n', '\n'), flush=True)
        # print('='*50)

    def _print_response(self, data: dict):
        print(f'< RESPONSE >'.center(50, '='))
        print(json.dumps(data, indent=2).replace('\\n', '\n'), flush=True)
        print('='*50)

    def _remove_notset_values(self, data: dict, sentinel: NOTSET = NOTSET):
        if isinstance(data, dict):
            keys_to_delete = []
            for key, value in data.items():
                if value is sentinel:
                    keys_to_delete.append(key)
                else:
                    data[key] = self._remove_notset_values(value, sentinel)
            for key in keys_to_delete:
                del data[key]
        elif isinstance(data, list):
            for i in range(len(data)):
                data[i] = self._remove_notset_values(data[i], sentinel)
        return data
