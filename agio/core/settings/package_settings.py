import copy
import inspect
import json
import re
import types
from typing import Any, Iterator, get_origin, get_args, Union, Type, Mapping, Sequence

from pydantic import BaseModel

from agio.core.exceptions import RequiredValueNotSetError
from agio.core.exceptions import SettingsInitError
from agio.core.settings.fields.base_field import BaseField
from agio.core.settings.fields.compaund_fields import CollectionField
from agio.core.settings.fields.model_fields import ModelField
from agio.core.settings.generic_types import REQUIRED
from agio.tools.json_serializer import JsonSerializer


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


def _extract_non_none_type(annotation: Any) -> Any:
    """Extract single non-None type from Optional/Union annotation."""
    origin = get_origin(annotation)
    if origin in (Union, types.UnionType):
        args = get_args(annotation)
        non_none_args = [arg for arg in args if arg is not type(None)]
        if len(non_none_args) == 1:
            return non_none_args[0]
    return None


def _iterate_pydantic_type_hints(model_class: Type[BaseModel]) -> Iterator[Any]:
    """
    Recursively iterates through all type hints of a Pydantic BaseModel's fields.
    Yields nested BaseModel types and generic type arguments for validation.
    """
    if not (isinstance(model_class, type) and issubclass(model_class, BaseModel)):
        raise TypeError("Input must be a Pydantic BaseModel class.")

    for field_info in model_class.model_fields.values():
        type_hint = field_info.annotation
        yield type_hint
        
        _yield_nested_types(type_hint)


def _yield_nested_types(type_hint: Any) -> Iterator[Any]:
    """Recursively yield nested types from a type hint."""
    origin = get_origin(type_hint)
    if not origin:
        return
    
    args = get_args(type_hint)
    
    if origin is Union or origin is types.UnionType:
        for arg in args:
            if arg is type(None):
                continue
            if isinstance(arg, type) and issubclass(arg, BaseModel):
                yield from _iterate_pydantic_type_hints(arg)
            else:
                yield arg
                yield from _yield_nested_types(arg)
    
    elif origin is tuple:
        for arg in args:
            if arg is Ellipsis:
                continue
            if isinstance(arg, type) and issubclass(arg, BaseModel):
                yield from _iterate_pydantic_type_hints(arg)
            else:
                yield arg
                yield from _yield_nested_types(arg)
    
    else:
        if isinstance(origin, type) and issubclass(origin, BaseModel):
            yield from _iterate_pydantic_type_hints(origin)
        for arg in args:
            if isinstance(arg, type) and issubclass(arg, BaseModel):
                yield from _iterate_pydantic_type_hints(arg)
            else:
                yield arg
                yield from _yield_nested_types(arg)


def _create_field_from_annotation(name: str, annotation: Any, default_value: Any = REQUIRED) -> BaseField:
    """Create a field instance based on a Python type annotation."""
    original_field_instance = None
    if isinstance(annotation, BaseField):
        original_field_instance = annotation
        annotation = annotation.field_type if hasattr(annotation, 'field_type') else type(annotation)

    origin = get_origin(annotation) or annotation
    args = get_args(annotation)

    # Handle Optional / Union types
    if origin in (Union, types.UnionType) and type(None) in args:
        non_none_args = [arg for arg in args if arg is not type(None)]
        if len(non_none_args) == 1:
            inner_type = non_none_args[0]
            field = _create_field_from_annotation(name, inner_type, default_value)
            if field:
                return field
            
            class NullableField(field.__class__):
                def _validate(self, value: Any) -> Any:
                    if value is None:
                        return None
                    return super()._validate(value)
            
            nullable_field = NullableField(default_value=default_value)
            nullable_field.field_type = annotation
            # Preserve collection field attributes
            for attr in ('element_type', 'element_types', '_key_type', '_value_type'):
                if hasattr(field, attr):
                    setattr(nullable_field, attr, getattr(field, attr))
            return nullable_field
        
        raise SettingsInitError(f"Union types with multiple non-None arguments are not directly supported yet: {annotation}")

    # Handle Generic types (list[T], dict[K,V], set[T], tuple[T, ...], etc.)
    if hasattr(origin, '__origin__') or origin in (list, set, dict, tuple):
        field_class = original_field_instance.__class__ if original_field_instance else _get_field_class_for_type(origin)
        if not field_class:
            raise SettingsInitError(f"Unsupported container type: {origin}")
        field = field_class(default_value)
        field.field_type = annotation
        if args:
            if origin in (list, set):
                field.element_type = args[0]
            elif origin is tuple:
                if len(args) == 2 and args[1] is ...:
                    field.element_type = args[0]
                else:
                    field.element_types = args
            elif origin is dict:
                field._key_type, field._value_type = args
        return field

    # Handle Pydantic BaseModel types
    if inspect.isclass(annotation) and issubclass(annotation, BaseModel):
        for hint in _iterate_pydantic_type_hints(annotation):
            if inspect.isclass(hint) and issubclass(hint, BaseField):
                raise TypeError(f"Field {name} in nested pydantic class cannot be instantiated from {annotation.__name__}. Use generic types instead.")
        field = ModelField(default_value, model=annotation)
        field.field_type = annotation
        return field

    # Handle Simple (non-generic, non-Pydantic) types
    field_class = original_field_instance.__class__ if original_field_instance else _get_field_class_for_type(origin)
    if field_class:
        field = field_class(default_value)
        field.field_type = annotation
        return field

    # Handle cases where the annotation itself is a BaseField subclass
    if inspect.isclass(annotation) and issubclass(annotation, BaseField):
        field = annotation(default_value=default_value)
        if not hasattr(field, 'field_type') or field.field_type is None:
            field.field_type = annotation.field_type if hasattr(annotation, 'field_type') else annotation
        return field
    
    raise ValueError(f"Unsupported annotation: {annotation}")


class _SettingsMeta(type):
    def __new__(mcs, name, bases, namespace, **kwargs):
        fields = {}
        annotations = namespace.get('__annotations__', {})
        
        # Process field instances from class namespace
        for attr_name, attr_value in namespace.items():
            if isinstance(attr_value, BaseField):
                field = copy.deepcopy(attr_value)
                field.set_name(attr_name)
                fields[attr_name] = field
        
        # set element_type for collection fields from annotations
        for field_name, field in fields.items():
            ann = annotations.get(field_name)
            if not ann:
                continue
            
            # extract inner type from Optional
            inner_type = _extract_non_none_type(ann)
            if inner_type:
                ann = inner_type
            
            origin = get_origin(ann)
            args = get_args(ann)
            if origin in (list, tuple, set) and args:
                field._element_type = args[0]

        # create fields from type annotations
        for attr_name, annotation in annotations.items():
            if attr_name in fields:
                continue
            default_value = namespace.get(attr_name, REQUIRED)
            if inspect.isclass(annotation) and issubclass(annotation, BaseField):
                annotation = annotation.field_type
            try:
                fields[attr_name] = _create_field_from_annotation(attr_name, annotation, default_value)
            except ValueError as e:
                raise ValueError(f"Error processing field '{attr_name}': {e}")

        # store fields in class
        new_ns = {k: v for k, v in namespace.items() if not isinstance(v, BaseField)}
        new_ns['_fields'] = fields
        new_ns['_kwargs'] = kwargs

        # store required fields in class
        required_fields = [name for name, field in fields.items() if field.is_required()]
        if required_fields:
            new_ns['_required_fields'] = required_fields

        return super().__new__(mcs, name, bases, new_ns)


class APackageSettings(metaclass=_SettingsMeta):
    __name_pattern = re.compile(r"^[a-z][a-z0-9_]+[a-z0-9]+$")

    def __init__(self, **kwargs):
        class_kwargs = {k: v for k, v in kwargs.items() if k.startswith('_')}
        self._kwargs = getattr(self, '_kwargs', {})
        self._name = ''
        self._fields_data = {}
        self._get_other_parm_func = class_kwargs.pop('_get_other_parm_func', None)
        self._solve_dependency_func = class_kwargs.pop('_solve_dependency_func', None)
        self._class_kwargs = class_kwargs
        
        package_name = kwargs.pop('_package_name', '')
        if package_name:
            self.set_name(package_name)
        
        for name, field in self._get_fields().items():
            field.set_name(name)
            field._dependency_callback = self._dependency_solver_requested
            self._fields_data[name] = field
            setattr(self, name, self._fields_data[name])
        
        if self._class_kwargs.get('_init_only'):
            return

        for name, value_data in kwargs.items():
            if name in self._fields_data:
                if isinstance(value_data, dict):
                    if 'value' in value_data:
                        self._fields_data[name].set(value_data['value'])
                    if 'dependency' in value_data:
                        dep = value_data['dependency']
                        if dep:
                            self._fields_data[name].set_dependency(dep)
                else:
                    self._fields_data[name].set(value_data)

    def __str__(self):
        return f"({', '.join(f'{name}={repr(getattr(self, name))}' for name in self._fields_data)})"

    def __repr__(self):
        return f"<{self.__class__.__name__}>"

    def get(self, param_name: str, **kwargs) -> Any:
        return self.get_parameter(param_name).get(**kwargs)

    def set(self, param_name: str, value: Any, **kwargs) -> None:
        if param_name not in self._fields_data:
            raise ValueError(f"Parameter '{param_name}' not found in {repr(self)}")
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

    @property
    def label(self):
        return self._kwargs.get('label') or self.__class__.__name__

    def find_parameter(self, name: str) -> BaseField:
        """Find a field by name"""
        return self._fields_data.get(name)

    def _get_fields(self) -> dict:
        """Return a dictionary of field names to field instances"""
        return getattr(self, '_fields', {})

    def iter_fields(self):
        yield from self._fields_data.items()

    def _dependency_solver_requested(self, field: BaseField, **kwargs) -> Any:
        if not self._solve_dependency_func:
            raise ValueError('Function for solve dependency not provided')
        return self._solve_dependency_func(field, self, **kwargs)

    def _check_missing_values(self):
        # check required fields first
        required_fields = getattr(self, '_required_fields', [])
        missing = [name for name in required_fields if not self._fields_data[name].has_value()]
        if missing:
            err_params = [f'{self.name}.{parm}' for parm in missing]
            raise RequiredValueNotSetError(
                f"Missing required fields in package settings: {', '.join(err_params)}"
                f"class: {inspect.getfile(self.__class__)}"
            )

    def __dump_values__(self, serialized:bool = False) -> dict:
        self._check_missing_values()
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

    def __dump_settings__(self, skip_default: bool = True) -> dict:
        self._check_missing_values()
        result = {}
        for name, field in self._fields_data.items():
            if skip_default and field.is_default():
                continue
            field_settings = field.get_settings()
            if field_settings:
                result[name] = self.__to_plain_data__(field_settings)
        return result

    @classmethod
    def __to_plain_data__(cls, obj):
        """Convert any Pydantic data to dict/list/primitives recursively"""
        if isinstance(obj, BaseModel):
            return cls.__to_plain_data__(obj.model_dump())
        elif isinstance(obj, Mapping):
            return {k: cls.__to_plain_data__(v) for k, v in obj.items()}
        elif isinstance(obj, Sequence) and not isinstance(obj, (str, bytes, bytearray)):
            return [cls.__to_plain_data__(v) for v in obj]
        else:
            return obj

    def __to_json__(self, serialize_hook=None, **kwargs) -> str:
        self._check_missing_values()
        JsonSerializer.custom_hook = serialize_hook
        return json.dumps(self.__dump_values__(serialized=True), cls=JsonSerializer, **kwargs)

    @classmethod
    def __schema__(cls) -> dict:
        """Ui schema for current package settings"""
        obj = cls(_init_only=True)
        parameters = {}
        for name, field in obj._fields_data.items():
            parameters[name] = field.get_schema()
        return parameters


