import json
from datetime import datetime
from pathlib import Path
from uuid import UUID

from agio.core import config
from agio.core.api.client.base import _ApiClientAuth


class ApiClient(_ApiClientAuth):
    _base_api_url = f'{config.api.PLATFORM_URL}/graphql'
    queries_root = Path(__file__).parent.parent.joinpath('queries')

    def _serialize_values(self, value: dict):
        data = json.dumps(value, cls=JsonSerializer)
        return json.loads(data)

    def make_query(self, query_file: str, **variables) -> dict:
        """Read query from file and execute query"""
        query_text = self._load_query(query_file)
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
                "variables": {k: v for k, v in variables if v is not None},
            })
        response = self.session.post(self._base_api_url, json=data)
        response.raise_for_status()
        return response.json()

    def _load_query(self, query_path: str) -> str:
        """
        Load GraphQL query from file
        """
        query_file_path = self.queries_root.joinpath(query_path).with_suffix('.graphql')
        if not query_file_path.exists():
            raise FileNotFoundError(f'Query file not found: {query_file_path}')
        return query_file_path.read_text()



class JsonSerializer(json.JSONEncoder):
    custom_hook = None

    def default(self, o):
        if isinstance(o, UUID):
            return str(o)
        elif isinstance(o, datetime):
            return o.isoformat()
        return super().default(o)