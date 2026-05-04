from agio.core import exceptions
from agio.core.api import client as default_client
from agio.core.api.utils import api_call


@api_call
def get_current_user(client=default_client):
    return client.make_query(
        'desk/account/getCurrentUserProfile'
    )['data']['currentUser']


@api_call
def get_user_by_id(user_id: str, client=default_client):
    return client.make_query(
        'desk/account/getUserById',
        id=user_id
    )['data']['user']


@api_call
def is_logged_in(client=default_client):
    try:
        get_current_user(client)
        return True
    except exceptions.RequestError:
        # message must be UNAUTHORIZED
        return False
