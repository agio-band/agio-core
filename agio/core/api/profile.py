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