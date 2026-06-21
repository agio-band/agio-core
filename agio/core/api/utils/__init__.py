from functools import wraps
from typing import Callable, ParamSpec, TypeVar

NOTSET = type("NotSetSentinel", (), {
    "__repr__": lambda self: "<NOTSET>",
    "__bool__": lambda self: False,
    "__nonzero__": lambda self: False,
    "__str__": lambda self: '',
})()

P = ParamSpec('P')
R = TypeVar('R')


def api_call(func: Callable[P, R]) -> Callable[P, R]:
    from agio.core.api import client

    # TODO add cache
    # TODO add logs

    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        # fix client argument
        if 'client' in kwargs:
            if kwargs['client'] is None:
                kwargs['client'] = client
        return func(*args, **kwargs)
    return wrapper
