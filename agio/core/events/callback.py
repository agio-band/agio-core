from functools import wraps


def callback(*callback_names, **kwargs):

    def decorator(func):

        @wraps
        def wrapper(*args, **kwargs):
            nonlocal func
            return func(*args, **kwargs)

        return wrapper

    return decorator