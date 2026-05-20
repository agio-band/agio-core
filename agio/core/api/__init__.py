import os

from .api_client.api_client import ApiClient

if os.environ.get('AGIO_USE_API_CLIENT_CONTEXT_PROXY'):
    from agio.tools.concurrent import ContextVarProxy
    client: ApiClient|ContextVarProxy = ContextVarProxy(ApiClient)
else:
    client = ApiClient()

from . import workspace, package, desk, auth, pipe, track, profile, drive
__all__ = ['client', 'workspace', 'package', 'desk', 'auth', 'pipe', 'track', 'profile', 'drive', 'ApiClient']
