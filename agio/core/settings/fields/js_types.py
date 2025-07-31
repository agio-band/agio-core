import traceback
import types
from inspect import isclass
from typing import (
    get_args,
    get_origin,
    Union,
    List,
    Dict,
    Tuple,
    Any,
)

from pydantic import BaseModel

BASE_TYPE_MAP = {
    str: "string",
    int: "number",
    float: "number",
    bool: "boolean",
    list: "array",
    type(None): "null",
    Any: "any",
}

UNION_TYPES = {Union, types.UnionType}



def to_js_type(python_type: Any) -> dict:
    from agio.core.settings import BaseField

    origin = get_origin(python_type) or python_type
    if origin is None:
        return {'field_type': 'null'}
    elif isclass(origin) and issubclass(origin, BaseModel):
        return {'field_type': 'model', 'type_schema': origin.model_json_schema()}
    elif isclass(origin) and issubclass(origin, BaseField):
        return to_js_type(origin.field_type)
    elif origin in (tuple, Tuple, list, List):
        args = get_args(python_type)
        field_info = {'field_type': 'array'}
        if len(set(args)) == 1:
            element_type = args[0]
            field_info['element_type'] = to_js_type(element_type)['field_type']
            if field_info['element_type'] == 'model':
                field_info['element_type_schema'] = element_type.model_json_schema()
        else:
            field_info['element_type'] = [to_js_type(a)['field_type'] for a in args]
        if len(args) > 1:
            field_info['element_count'] = len(args)
        return field_info
    elif origin in BASE_TYPE_MAP:
        return {'field_type': BASE_TYPE_MAP[origin]}
    elif origin in UNION_TYPES:
        arg = [x for x in get_args(python_type) if x][0]
        return {'field_type': to_js_type(arg)}
    elif origin in (dict, Dict):
        info = {'field_type': 'object'}
        args = get_args(python_type)
        if args:
            # first value always string
            info['element_type'] = to_js_type(args[-1])['field_type']
        return info
    return {'field_type': str(python_type).replace('typing.', '').replace('NoneType', 'null').lower()}
