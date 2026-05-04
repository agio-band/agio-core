from agio.core.api.utils import api_call
from agio.core.exceptions import RequestError
from requests.exceptions import HTTPError
from agio.core.api import client as default_client


# auth
@api_call
def login(client=default_client):
    client.login()


@api_call
def logout(client=default_client):
    client.logout()


@api_call
def is_logged_in(client=default_client):
    """
    Check current user is logged in
    """
    try:
        resp = client.make_query('desk/account/currentUserId')
    except (HTTPError, RequestError):
        return False
    return 'error' not in resp
