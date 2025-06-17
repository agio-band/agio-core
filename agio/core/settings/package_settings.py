import json
import re
import types
import copy
import inspect
from typing import Any, Iterator, get_origin, get_args, Union, Type, List, Dict, Optional
from pydantic import BaseModel, Field
from pydantic_core._pydantic_core import PydanticUndefined

from .exceptions import RequiredValueNotSetError
from .fields.base_field import BaseField
from .fields.compaund_fields import CollectionField
from .fields.model_fields import ModelField
from .generic_types import REQUIRED
from .serializers import JsonSerializer


def _get_field_class_for_type(python_type: type, args: tuple = None) -> Type[BaseField] | None:
    """finding correct class for specified Python type"""
    if not isinstance(python_type, type):
        return None
    # collect classes with field_type attribute
    field_classes = [
        cls for cls in BaseField.__subclasses__() + CollectionField.__subclasses__()
        if hasattr(cls, 'field_type') and cls.field_type is not None
    ]
    # check type match
    for cls in field_classes:
        cls_origin = get_origin(cls.field_type) or cls.field_type
        if cls_origin == python_type or cls == python_type:
            return cls
    # field_type is abc type
    for cls in field_classes:
        cls_origin = get_origin(cls.field_type) or cls.field_type
        if issubclass(python_type, cls_origin):
            return cls
    return None


def _iterate_pydantic_type_hints(model_class: Type[BaseModel]) -> Iterator[Any]:
    """
    Recursively iterates through all type hints of a Pydantic BaseModel's fields.
    This includes nested Pydantic models, generic types (list, dict, tuple),
    and their contained type arguments.

    Args:
        model_class: The Pydantic BaseModel class to inspect.

    Yields:
        Each type hint encountered (e.g., str, int, list[str], Optional[MyNestedModel],
        and also the 'str' and 'int' from dict[str, int]).
    """
    if not (isinstance(model_class, type) and issubclass(model_class, BaseModel)):
        raise TypeError("Input must be a Pydantic BaseModel class.")

    for field_name, field_info in model_class.model_fields.items():
        type_hint = field_info.annotation

        # Yield the top-level type hint for the current field
        yield type_hint

        # Get the origin and arguments of the type hint
        origin = get_origin(type_hint)
        args = get_args(type_hint)

        if origin:  # This indicates a generic type (e.g., List, Dict, Union, Optional, Tuple)
            if origin is Union or origin is types.UnionType:
                for arg in args:
                    # Skip NoneType when iterating Union arguments for practical purposes,
                    # as it's typically handled by Optional.
                    if arg is type(None):
                        continue

                    if isinstance(arg, type) and issubclass(arg, BaseModel):
                        yield from _iterate_pydantic_type_hints(arg)
                    else:
                        # Recursively process and yield arguments of nested generics
                        yield from _process_nested_type_hint(arg)

            elif origin is tuple:
                for arg in args:
                    # tuple[Type, ...] -> arg will be 'Type' and then '...'
                    if arg is Ellipsis:  # Handle Tuple[Type, ...]
                        continue  # The 'Type' was already processed in the previous iteration

                    if isinstance(arg, type) and issubclass(arg, BaseModel):
                        yield from _iterate_pydantic_type_hints(arg)
                    else:
                        # Recursively process and yield arguments of nested generics
                        yield from _process_nested_type_hint(arg)

            # Handles List, Dict, Set, and any other generic where the origin itself
            # might be a BaseModel (less common, but covered) or for which we need
            # to iterate through its arguments.
            else:  # Covers list, dict, set, etc.
                # If the origin itself is a BaseModel (e.g., if a generic was defined with a BaseModel as origin)
                if isinstance(origin, type) and issubclass(origin, BaseModel):
                    yield from _iterate_pydantic_type_hints(origin)

                # Process the arguments (e.g., str and int from Dict[str, int])
                for arg in args:
                    if isinstance(arg, type) and issubclass(arg, BaseModel):
                        yield from _iterate_pydantic_type_hints(arg)
                    else:
                        # Recursively process and yield arguments of nested generics
                        yield from _process_nested_type_hint(arg)

        # If the top-level type hint is itself a Pydantic model (not a generic container)
        elif isinstance(type_hint, type) and issubclass(type_hint, BaseModel):
            yield from _iterate_pydantic_type_hints(type_hint)


def _process_nested_type_hint(nested_hint: Any) -> Iterator[Any]:
    """Helper function to process and yield from nested type hints."""
    yield nested_hint  # Yield the nested hint itself

    nested_origin = get_origin(nested_hint)
    nested_args = get_args(nested_hint)

    if nested_origin:
        # Handle cases like List[Union[str, int]]
        if nested_origin is Union or nested_origin is types.UnionType:
            for nested_arg in nested_args:
                if nested_arg is type(None):
                    continue
                if isinstance(nested_arg, type) and issubclass(nested_arg, BaseModel):
                    yield from _iterate_pydantic_type_hints(nested_arg)
                else:
                    yield from _process_nested_type_hint(nested_arg)  # Recurse for deeper nesting
        elif nested_origin is tuple:  # Special handling for tuples within other generics
            for nested_arg in nested_args:
                if nested_arg is Ellipsis:
                    continue
                if isinstance(nested_arg, type) and issubclass(nested_arg, BaseModel):
                    yield from _iterate_pydantic_type_hints(nested_arg)
                else:
                    yield from _process_nested_type_hint(nested_arg)  # Recurse for deeper nesting
        else:  # Other generics (list, dict, set)
            if isinstance(nested_origin, type) and issubclass(nested_origin, BaseModel):
                yield from _iterate_pydantic_type_hints(nested_origin)
            for nested_arg in nested_args:
                if isinstance(nested_arg, type) and issubclass(nested_arg, BaseModel):
                    yield from _iterate_pydantic_type_hints(nested_arg)
                else:
                    yield from _process_nested_type_hint(nested_arg)  # Recurse for deeper nesting


def _create_field_from_annotation(name: str, annotation: Any, default_value: Any = REQUIRED) -> BaseField:
    """
    Creates a field instance (BaseField) based on a Python type annotation.

    Args:
        name: The name of the field.
        annotation: The Python type annotation (e.g. int, list[str], Optional[MyModel]).
        default_value: The default value for the field, or REQUIRED if the field is required.

    Returns:
        An instance of a class that extends BaseField.

    Raises:
        ValueError: If the annotation is not supported.
    """
    original_field_instance = None
    # If the annotation is already a field instance (e.g., `x: IntField = IntField(...)`)
    if isinstance(annotation, BaseField):
        original_field_instance = annotation
        # Use the field_type of the provided field instance for further processing
        annotation = annotation.field_type if hasattr(annotation, 'field_type') else type(annotation)

    origin = get_origin(annotation) or annotation
    args = get_args(annotation)

    # --- Handle Optional / Union types ---
    if origin in (Union, types.UnionType) and type(None) in args:
        non_none_args = [arg for arg in args if arg is not type(None)]
        if len(non_none_args) == 1:
            # Recursively create the field for the non-None type
            field = _create_field_from_annotation(name, non_none_args[0], default_value)

            # Create a NullableField wrapper that allows None
            class NullableField(field.__class__):
                def _validate(self, value: Any) -> Any:
                    if value is None:
                        return None
                    return super()._validate(value)

            # Ensure the NullableField retains the correct original field_type
            nullable_field = NullableField(default_value=default_value)
            nullable_field.field_type = annotation  # Set to the original Union type
            return nullable_field
        # If Union has multiple non-None types, it's more complex and might need a dedicated UnionField
        raise ValueError(f"Union types with multiple non-None arguments are not directly supported yet: {annotation}")

    # --- Handle Generic types (list[T], dict[K,V], set[T], tuple[T, ...], etc.) ---
    # Check for __origin__ for typing.List, typing.Dict etc. or direct built-in types
    if hasattr(origin, '__origin__') or origin in (list, set, dict, tuple):
        # Find the appropriate field class (e.g., ListField, DictField)
        field_class = original_field_instance.__class__ if original_field_instance else _get_field_class_for_type(
            origin, args)
        if not field_class:
            raise ValueError(f"Unsupported container type: {origin}")
        # Create an instance of the specific collection field
        field = field_class(default_value)
        # This ensures 'dict[str, int]' is stored, not just 'dict'
        field.field_type = annotation
        # Set argument types for collections (e.g., element_type for list, key/value for dict)
        if args:
            if origin in (list, set):
                field.element_type = args[0]
            elif origin is tuple:
                if len(args) == 2 and args[1] is ...:  # Tuple[T, ...]
                    field.element_type = args[0]
                else:  # Tuple[T1, T2, ...]
                    field.element_types = args
            elif origin is dict:
                field._key_type, field._value_type = args

        return field

    # --- Handle Pydantic BaseModel types ---
    if inspect.isclass(annotation) and issubclass(annotation, BaseModel):
        for hint in _iterate_pydantic_type_hints(annotation):
            if inspect.isclass(hint) and issubclass(hint, BaseField):
                raise TypeError(f"Field {name} in nested pydantic class cannot be instantiated from {annotation.__name__}. Use generic types instead.")
        field = ModelField(default_value, model=annotation)
        field.field_type = annotation
        return field

    # --- Handle Simple (non-generic, non-Pydantic) types ---
    field_class = original_field_instance.__class__ if original_field_instance else _get_field_class_for_type(origin,
                                                                                                              args)
    if field_class:
        field = field_class(default_value=default_value)
        # Ensure simple types also store their direct annotation as field_type
        field.field_type = annotation
        return field

    # --- Handle cases where the annotation itself is a BaseField subclass ---
    if inspect.isclass(annotation) and (
    issubclass(annotation, BaseField)):  # Removed CollectionField as it's a BaseField subclass
        # If the annotation is a field class, instantiate it.
        field = annotation(default_value=default_value)
        if not hasattr(field, 'field_type') or field.field_type is None:
            # Attempt to infer if field_type wasn't set by the field's own init/class
            field.field_type = annotation.field_type if hasattr(annotation, 'field_type') else annotation
        return field

    raise ValueError(f"Unsupported annotation: {annotation}")


class _SettingsMeta(type):
    def __new__(mcs, name, bases, namespace):
        fields = {}
        annotations = namespace.get('__annotations__', {})

        # Process explicit field instances
        for attr_name, attr_value in namespace.items():
            if isinstance(attr_value, BaseField):
                field = copy.deepcopy(attr_value)
                field.set_name(attr_name)
                fields[attr_name] = field
        # Process type annotations
        for attr_name, annotation in annotations.items():
            if attr_name in fields:
                continue
            default_value = namespace.get(attr_name, REQUIRED)
            if issubclass(annotation, BaseField):
                annotation = annotation.field_type
            try:
                fields[attr_name] = _create_field_from_annotation(attr_name, annotation, default_value)
            except ValueError as e:
                raise ValueError(f"Error processing field '{attr_name}': {e}")

        # Store fields in class
        new_ns = {k: v for k, v in namespace.items() if not isinstance(v, BaseField)}
        new_ns['_fields'] = fields

        # Store required fields in class
        required_fields = [name for name, field in fields.items() if field.is_required()]
        if required_fields:
            new_ns['_required_fields'] = required_fields

        return super().__new__(mcs, name, bases, new_ns)


class APackageSettings(metaclass=_SettingsMeta):
    __name_pattern = re.compile(r"^[a-z][a-z0-9_]+[a-z0-9]+$")

    def __init__(self, **kwargs):
        class_kwargs = {k: v for k, v in kwargs.items() if k.startswith('_')}
        self._label = kwargs.pop('_label', None)
        self._help_text = kwargs.pop('_help_text', None)
        self._description = kwargs.pop('_description', None)
        self._layout = kwargs.pop('_layout', None)
        self._name = ''
        self._fields_data = {}
        self._get_other_parm_func = class_kwargs.pop('_get_other_parm_func', None)
        self._class_kwargs = class_kwargs
        # Initialize fields from class
        package_name = kwargs.pop('_package_name', '')
        if package_name:
            self.set_name(package_name)
        for name, field in self._get_fields().items():
            self._fields_data[name] = copy.deepcopy(field)
            # self._fields_data[name]._set_parent_settings(self)
            setattr(self, name, self._fields_data[name])
        if self._class_kwargs.get('_init_only'):
            return
        # Check required fields first
        required_fields = getattr(self, '_required_fields', [])
        missing = [name for name in required_fields if name not in kwargs and not self._fields_data[name].has_value()]

        if missing:
            raise RequiredValueNotSetError(f"Missing required fields in package settings \"{self.name}\": {', '.join(missing)}")

        # Set values
        for name, value_data in kwargs.items():
            if name in self._fields_data:
                if isinstance(value_data, dict):
                    # from settings file
                    if 'value' in value_data:
                        self._fields_data[name].set(value_data['value'])
                    if 'dependency' in value_data:
                        self._fields_data[name].dependency(value_data['dependency'])
                else:
                    # from simple values without extra parameters
                    self._fields_data[name].set(value_data)



    def __str__(self):
        return f"({', '.join(f'{name}={repr(getattr(self, name))}' for name in self._fields_data)})"

    def __repr__(self):
        return f"<{self.__class__.__name__}>"

    def get(self, param_name: str, **kwargs) -> Any:
        return self.get_parameter(param_name).get(**kwargs)

    def set(self, param_name: str, value: Any, **kwargs) -> None:
        if param_name not in self._fields_data:
            raise ValueError(f"Parameter '{param_name}' not found")
        self._fields_data[param_name].set(value, **kwargs)

    def get_parameter(self, param_name: str) -> Type[BaseField]:
        if param_name not in self._fields_data:
            raise ValueError(f"Parameter '{param_name}' not found")
        return self._fields_data[param_name]

    def _get_other_parm(self, parm_name: str) -> Type[BaseField]:
        if self._get_other_parm_func:
            return self._get_other_parm_func(parm_name)
        raise ValueError(f"No function to get related parameter")

    @property
    def name(self) -> str:
        return self._name

    def set_name(self, name: str) -> None:
        if not isinstance(name, str):
            raise TypeError("Name must be a string")
        if not self.__name_pattern.match(name):
            raise ValueError(f"Invalid name: {name}")
        self._name = name

    def find_parameter(self, name: str) -> BaseField:
        """Find a field by name"""
        return self._fields_data.get(name)

    def _get_fields(self) -> dict:
        """Return a dictionary of field names to field instances"""
        return getattr(self, '_fields', {})

    def iter_fields(self):
        yield from self._fields_data.items()

    def __dump_values__(self, serialized:bool = False) -> dict:
        result = {}
        for name, field in self._fields_data.items():
            try:
                value = field.get_serialized() if serialized else field.get()
                if value is not None or field.is_required():
                    result[name] = value
            except ValueError as e:
                if field.is_required():
                    raise ValueError(f"Field '{name}' is required but has no value") from e
        return result

    def __dump_settings__(self) -> dict:
        result = {}
        for name, field in self._fields_data.items():
            result[name] = field.get_settings()
        return result

    def __to_json__(self, serialize_hook=None, **kwargs) -> str:
        JsonSerializer.custom_hook= serialize_hook
        return json.dumps(self.__dump_values__(serialized=True), cls=JsonSerializer, **kwargs)

    @classmethod
    def __schema__(cls) -> dict:
        obj = cls(_init_only=True)
        parameters = {}
        for name, field in obj._fields_data.items():
            field_schema = field.get_schema()
            # field_schema['field_type'] = field.__class__.__name__
            parameters[name] = field_schema
        return {
            'parameters': parameters,
            'name': obj.name
        }


