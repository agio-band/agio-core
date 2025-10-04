from oauthlib.oauth2.rfc6749.errors import InvalidGrantError
from agio.core import exceptions
from . import client


def get_current_user():
    return client.make_query(
        'desk/account/getCurrentUserProfile'
    )['data']['currentUser']


def get_user_by_id(user_id: str):
    return client.make_query(
        'desk/account/getUserById',
        id=user_id
    )['data']['user']

def is_logged_in():
    try:
        get_current_user()
        return True
    except (exceptions.RequestError, InvalidGrantError):
        # message must be UNAUTHORIZED
        return False