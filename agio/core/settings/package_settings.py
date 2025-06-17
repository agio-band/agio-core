import json
import re
import types
import copy
import inspect
from pydantic import BaseModel
from typing import Any, get_origin, get_args, Type,Union
from weakref import ref
from .exceptions import RequiredValueNotSetError
from .fields.base_field import BaseField
from .fields.compaund_fields import CollectionField
from .fields.model_fields import ModelField
from .generic_types import REQUIRED
from .serializers import JsonSerializer


# Special markers


def _get_field_class_for_type(python_type: type, args: tuple = None) -> Type[BaseField] | None:
    """Находит подходящий класс поля для указанного типа Python"""
    if not isinstance(python_type, type):
        return None
    # Собираем все классы полей, которые имеют field_type
    field_classes = [
        cls for cls in BaseField.__subclasses__() + CollectionField.__subclasses__()
        if hasattr(cls, 'field_type') and cls.field_type is not None
    ]
    # Проверяем точное соответствие типов
    for cls in field_classes:
        cls_origin = get_origin(cls.field_type) or cls.field_type
        if cls_origin == python_type or cls == python_type:
            return cls
    # Проверяем наследование (для случаев, когда field_type - абстрактный тип)
    for cls in field_classes:
        cls_origin = get_origin(cls.field_type) or cls.field_type
        if issubclass(python_type, cls_origin):
            return cls
    return None


def _create_field_from_annotation(name: str, annotation: Any, default_value: Any = REQUIRED) -> BaseField:
    original_field = None
    if hasattr(annotation, 'field_type'):
        original_field = annotation
        annotation = annotation.field_type
    origin = get_origin(annotation) or annotation
    args = get_args(annotation)

    # Обработка Optional/Union[Something, None]
    if origin in (Union, types.UnionType) and type(None) in args:
        non_none_args = [arg for arg in args if arg is not type(None)]
        if len(non_none_args) == 1:
            field = _create_field_from_annotation(name, non_none_args[0], default_value)

            class NullableField(field.__class__):
                def _validate(self, value: Any) -> Any:
                    if value is None:
                        return None
                    return super()._validate(value)

            return NullableField(default_value=default_value)

    # Для Generic типов (list[T], dict[K,V], set[T] и т.д.)
    if hasattr(origin, '__origin__') or origin in (list, set, dict, tuple):
        field_class = original_field or _get_field_class_for_type(origin, args)
        if not field_class:
            raise ValueError(f"Unsupported container type: {origin}")

        # Создаем инстанс поля
        field = field_class(default_value)

        # Для Generic полей устанавливаем типы аргументов
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

        # Не перезаписываем field_type, так как он уже установлен в классе поля
        return field

    # Для Pydantic моделей
    if inspect.isclass(annotation) and issubclass(annotation, BaseModel):
        return ModelField(default_value, model=annotation)

    # Для простых типов
    field_class = original_field or _get_field_class_for_type(origin, args)
    if field_class:
        return field_class(default_value=default_value)

    # Для случаев, когда аннотация - это сам класс поля (не рекомендуется)
    if inspect.isclass(annotation) and (
            issubclass(annotation, BaseField) or issubclass(annotation, CollectionField)):
        return annotation(default_value=default_value)

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
            field_schema['field_type'] = field.__class__.__name__
            parameters[name] = field_schema
        return {
            'parameters': parameters,
            'name': obj.name
        }


