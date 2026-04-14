from functools import wraps

from agio.core.api import client as default_client


def set_client(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if 'client' in kwargs:
            if kwargs['client'] is None:
                kwargs['client'] = default_client
        return func(*args, **kwargs)
    return wrapper
