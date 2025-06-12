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
    resp = client.make_query('desk/account/currentUserId')
    return 'error' not in resp
