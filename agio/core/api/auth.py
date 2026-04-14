from requests.exceptions import HTTPError
from agio.core.exceptions import RequestError
from . import client as default_client
from agio.core.api._utils import set_client


# auth
@set_client
def login(client=default_client):
    client.login()


@set_client
def logout(client=default_client):
    client.logout()


@set_client
def is_logged_in(client=default_client):
    """
    Check current user is logged in
    """
    try:
        resp = client.make_query('desk/account/currentUserId')
    except (HTTPError, RequestError):
        return False
    return 'error' not in resp
