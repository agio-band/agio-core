import json
import logging
import os
from datetime import datetime
from pathlib import Path
from uuid import UUID

from requests.exceptions import HTTPError

from agio.core.api.api_client.base import _ApiClientAuth
from agio.core.api.utils import NOTSET
from agio.core.exceptions import RequestError
from agio.core.utils import config

logger = logging.getLogger(__name__)


class ApiClient(_ApiClientAuth):
    _base_api_url = f'{config.API.PLATFORM_URL}/graphql'
    queries_root = Path(__file__).parent.parent.joinpath('queries')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._debug_query = bool(os.getenv('AGIO_DEBUG_QUERY'))

    def set_debug_query(self, val: bool):
        self._debug_query = bool(val)

    def _serialize_values(self, value: dict):
        data = json.dumps(value, cls=JsonSerializer)
        return json.loads(data)

    def make_query(self, query_file: str, **variables) -> dict:
        """Read query from file and execute query"""
        query_text = self._load_query(query_file)
        variables = self._remove_notset_values(variables)
        variables = self._serialize_values(variables)
        return self.make_query_raw(query_text, **variables)

    def make_query_raw(self, query: str, **variables) -> dict:
        """Execute query from string"""
        self.check_is_expire()
        data = {
            "query": query,
        }
        if variables:
            data.update({
                "variables": {k: v for k, v in variables.items() if v is not None},
            })
        if self._debug_query:
            self._print_data(data, "Request")
        response = self.session.post(self._base_api_url, json=data)
        if not response.ok:
            logger.exception(f"Request failed with status code: {response.status_code}")
        try:
            response.raise_for_status()
        except HTTPError as e:
            raise RequestError(f'Request failed: {response.text}') from e
        result = response.json()
        if self._debug_query:
            self._print_data(result, 'Response')
        if 'errors' in result:
            raise RequestError('\n'.join(x['message'] for x in result['errors']))
        return result

    def _load_query(self, query_path: str) -> str:
        """
        Load GraphQL query from file
        """
        query_file_path = self.queries_root.joinpath(query_path).with_suffix('.graphql')
        if not query_file_path.exists():
            raise FileNotFoundError(f'Query file not found: {query_file_path}')
        return query_file_path.read_text()

    def _print_data(self, data: dict, caption: str):
        print(f' {caption} '.center(50, '='))
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

class JsonSerializer(json.JSONEncoder):
    custom_hook = None

    def default(self, o):
        if isinstance(o, UUID):
            return str(o)
        elif isinstance(o, datetime):
            return o.isoformat()
        return super().default(o)