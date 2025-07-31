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


# def type_hint_to_js(py_type) -> Any:
#     from agio.core.settings import BaseField
#
#     origin = get_origin(py_type)
#     args = get_args(py_type)
#
#     # Annotated[T, ...]
#     if origin is Annotated:
#         return type_hint_to_js(args[0])
#
#     # Union / Optional / T | None
#     if origin in UNION_TYPES:
#         js_types = [type_hint_to_js(t) for t in args]
#         return js_types
#
#     # list[T] or list[T1, T2]
#     if origin in (list, List):
#         if args:
#             item_types = [type_hint_to_js(a) for a in args]
#             return item_types if len(item_types) > 1 else [item_types[0]]
#         return ["any"]
#
#     # dict[K, V]
#     if origin in (dict, Dict):
#         key = type_hint_to_js(args[0]) if args else "string"
#         val = type_hint_to_js(args[1]) if len(args) > 1 else "any"
#         return {key: val}
#
#     # tuple[T1, T2, ...]
#     if origin in (tuple, Tuple):
#         return [type_hint_to_js(a) for a in args]
#
#     # Literal
#     if origin is Literal:
#         return list(args)
#
#     # primitives
#     if py_type in BASE_TYPE_MAP:
#         return BASE_TYPE_MAP[py_type]
#
#     # Pydantic model
#     if isinstance(py_type, type) and issubclass(py_type, BaseModel):
#         return model_to_js_schema(py_type)
#
#     # settings field
#     if origin and issubclass(origin, BaseField):
#         return to_js_type(origin.field_type)
#     # Pydantic or custom types (EmailStr, HttpUrl...)
#     if isinstance(py_type, type):
#         return py_type.__name__
#
#     return "object"


# def model_to_js_schema(model_cls: type) -> dict:
#     hints = get_type_hints(model_cls, include_extras=True)
#     return {name: to_js_type(hint)['field_type'] for name, hint in hints.items()}


# def to_js_type1(type_hint: Any) -> Any:
#     from agio.core.settings import BaseField
#
#     origin = get_origin(type_hint)
#     if issubclass(type_hint, BaseModel):
#         return model_to_js_schema(type_hint)
#     elif origin and isclass(origin) and issubclass(origin, BaseField):
#         return to_js_type(type_hint.field_type)
#     else:
#         return type_hint_to_js(type_hint)


def to_js_type(python_type: Any) -> dict:
    """
    Fields:
        field_type
        element_type
        element_type_schema
        element_count
    """
    from agio.core.settings import BaseField
    origin = get_origin(python_type) or python_type
    if origin is None:
        return {'field_type': 'null'}
    elif isclass(origin) and issubclass(origin, BaseModel):
        return {'field_type': 'model'}#, 'type_schema': origin.model_json_schema()}
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
            info['element_type'] = to_js_type(args[-1])['field_type']
        return info
    return {'field_type': str(python_type).replace('typing.', '').replace('NoneType', 'null').lower()}
