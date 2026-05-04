from functools import wraps


NOTSET = type("NotSetSentinel", (), {
    "__repr__": lambda self: "<NOTSET>",
    "__bool__": lambda self: False,
    "__nonzero__": lambda self: False,
    "__str__": lambda self: '',
})()


def api_call(func):
    from agio.core.api import client

    # TODO add cache
    # TODO add logs

    @wraps(func)
    def wrapper(*args, **kwargs):
        # fix client argument
        if 'client' in kwargs:
            if kwargs['client'] is None:
                kwargs['client'] = client
        return func(*args, **kwargs)
    return wrapper
