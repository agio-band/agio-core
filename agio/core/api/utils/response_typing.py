from typing import Callable, Type
from pydantic import BaseModel
from agio.core import config


Schema = Type[BaseModel]


def response_schema(schema: Schema) -> Callable:
    def decorator(func: Callable) -> Callable:
        if config.api.USE_RESPONSE_SCHEMA:
            def wrapper(*args, **kwargs) -> BaseModel:
                result = func(*args, **kwargs)
                if not isinstance(result, dict):
                    raise TypeError('Return value is not a dict')
                return schema(**result)
            return wrapper
        else:
            return func
    return decorator
