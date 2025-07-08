from oauthlib.oauth2.rfc6749.errors import InvalidGrantError
from . import client

# auth

def login():
    client.login()


def logout():
    client.logout()


def is_logged_in():
    """
    Check current user is logged in
    """
    try:
        resp = client.make_query('desk/account/currentUserId')
    except InvalidGrantError:
        return False
    return 'error' not in resp
