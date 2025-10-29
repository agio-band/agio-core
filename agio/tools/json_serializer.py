import json
from collections import defaultdict
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

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

