import os

from .api_client.api_client import ApiClient

if os.environ.get('AGIO_USE_API_CLIENT_THREAD_PROXY'):
    from agio.tools.concurrent import ThreadContextProxy
    client: ApiClient|ThreadContextProxy = ThreadContextProxy(ApiClient)
elif os.environ.get('AGIO_USE_API_CLIENT_ASYNC_PROXY'):
    from agio.tools.concurrent import AsyncContextProxy
    client: ApiClient | AsyncContextProxy = AsyncContextProxy(ApiClient)
else:
    client = ApiClient()

from . import workspace, package, desk, auth, pipe, track, profile, drive
__all__ = ['client', 'workspace', 'package', 'desk', 'auth', 'pipe', 'track', 'profile', 'drive', 'ApiClient']
