import json
from datetime import datetime

from pydantic import BaseModel

from agio.core.exceptions import NotSupportedTypeError


class JsonSerializer(json.JSONEncoder):
    custom_hook = None

    def default(self, o):
        if isinstance(o, BaseModel):
            return o.model_dump()
        elif isinstance(o, datetime):
            return o.isoformat()
        if self.__class__.custom_hook:
            try:
                return self.__class__.custom_hook(o)
            except NotSupportedTypeError:
                pass
        return super().default(o)


def custom_serialize_hook(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise NotSupportedTypeError
