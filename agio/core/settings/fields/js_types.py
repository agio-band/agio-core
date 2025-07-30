import types
from inspect import isclass

from pydantic import BaseModel
from typing import (
    get_args,
    get_origin,
    Union,
    List,
    Dict,
    Tuple,
    Literal,
    Annotated,
    Any,
    get_type_hints,
)


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


def type_hint_to_js(py_type) -> Any:


    origin = get_origin(py_type)
    args = get_args(py_type)

    # Annotated[T, ...]
    if origin is Annotated:
        return type_hint_to_js(args[0])

    # Union / Optional / T | None
    if origin in UNION_TYPES:
        js_types = [type_hint_to_js(t) for t in args]
        return js_types

    # list[T] or list[T1, T2]
    if origin in (list, List):
        if args:
            item_types = [type_hint_to_js(a) for a in args]
            return item_types if len(item_types) > 1 else [item_types[0]]
        return ["any"]

    # dict[K, V]
    if origin in (dict, Dict):
        key = type_hint_to_js(args[0]) if args else "string"
        val = type_hint_to_js(args[1]) if len(args) > 1 else "any"
        return {key: val}

    # tuple[T1, T2, ...]
    if origin in (tuple, Tuple):
        return [type_hint_to_js(a) for a in args]

    # Literal
    if origin is Literal:
        return list(args)

    # primitives
    if py_type in BASE_TYPE_MAP:
        return BASE_TYPE_MAP[py_type]

    # Pydantic model
    if isinstance(py_type, type) and issubclass(py_type, BaseModel):
        return model_to_js_schema(py_type)

    # Pydantic or custom types (EmailStr, HttpUrl...)
    if isinstance(py_type, type):
        return py_type.__name__

    return "object"


def model_to_js_schema(model_cls: type) -> dict:
    hints = get_type_hints(model_cls, include_extras=True)
    return {name: type_hint_to_js(hint) for name, hint in hints.items()}


def to_js_type1(type_hint: Any) -> Any:
    from agio.core.settings import BaseField

    origin = get_origin(type_hint)
    if issubclass(type_hint, BaseModel):
        return model_to_js_schema(type_hint)
    elif origin and isclass(origin) and issubclass(origin, BaseField):
        return to_js_type(type_hint.field_type)
    else:
        return type_hint_to_js(type_hint)


def to_js_type(python_type: Any) -> str:
    from agio.core.settings import BaseField
    origin = get_origin(python_type) or python_type
    if origin is str:
        return "string"
    if origin is int:
        return "integer"
    if origin is float:
        return "number"
    if origin is bool:
        return "boolean"
    if origin is list:
        return "array"
    if origin is dict:
        return "object"
    if issubclass(origin, BaseModel):
        return "model"
    if issubclass(origin, BaseField):
        return to_js_type(origin.field_type)
    return str(python_type).replace('typing.', '').replace('NoneType', 'null').lower()
