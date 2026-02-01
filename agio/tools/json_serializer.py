import json
from collections import defaultdict
from datetime import datetime
from typing import Any, Callable
from uuid import UUID

from pydantic import BaseModel
from pydantic import TypeAdapter

from agio.core.exceptions import NotSupportedTypeError


class JsonSerializer(json.JSONEncoder):
    custom_hook = None

    def default(self, o):
        if isinstance(o, BaseModel):
            return o.model_dump()
        elif isinstance(o, datetime):
            return o.isoformat()
        elif isinstance(o, UUID):
            return str(o)
        elif isinstance(o, defaultdict):
            return dict(o)
        if self.__class__.custom_hook:
            try:
                return self.__class__.custom_hook(o)
            except NotSupportedTypeError:
                pass
        return super().default(o)


def to_simple_dict(obj: Any, default: Callable = None):
    """
    Recursive convert nested object to simple types with callback for custom types.
    Example
    >>> def my_callback(obj):
    >>>     if hasattr(obj, 'to_dict'):
    >>>         return obj.to_dict()
    >>>     raise TypeError
    >>> my_dict = {...}
    >>> correct_dict = to_simple_dict(my_dict, my_callback)
    """
    adapter = TypeAdapter(Any)

    def handle_custom(val):
        if default:
            return default(val)
        raise TypeError(f"Object of type {val.__class__.__name__} is not JSON serializable")

    return adapter.dump_python(
        obj,
        mode='json',
        fallback=handle_custom
    )
