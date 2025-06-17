import builtins
import inspect
import re
import types
from abc import ABC, ABCMeta
from functools import cached_property
from typing import Any, Callable, Type, Union, Sequence, List
from weakref import ref
from pydantic import TypeAdapter, BaseModel
from pydantic_core import ValidationError

from agio.core.settings.exceptions import ValueTypeError
from agio.core.settings.fields.js_types import to_js_type
from agio.core.settings.generic_types import REQUIRED, NOT_SET
from agio.core.settings.validators import ValidatorBase
from agio.core.utils.text_utils import unslugify

ValidatorInstance = ValidatorBase
ValidatorFactory = Callable[..., ValidatorBase]
ValidatorClass = Type[ValidatorBase]

ValidatorType = Union[ValidatorInstance, ValidatorFactory, ValidatorClass]


class BaseFieldMeta(ABCMeta):
    def __new__(mcs, name, bases, namespace, **kwargs):
        cls = super().__new__(mcs, name, bases, namespace)
        cls._creation_flags = kwargs
        return cls


class BaseField(ABC, metaclass=BaseFieldMeta):
    field_type: Any = None
    # value_type: Any = None
    default_validators: list[ValidatorBase, ...] = []
    __name_pattern = re.compile(r'^[a-zA-Z](?:[a-zA-Z0-9_]*[a-zA-Z0-9])?$')

    def __init__(
        self,
        default_value: Any = REQUIRED,
        *,
        validators: list[ValidatorBase, ...] = None,
        label: str = None,
        description: str = None,
        docs_url: str = None,
        widget: str|dict = None,
        order: dict = None,
        hint: str = None,
        **kwargs
    ):
        self._data: dict[str, Any] = {
            'value': NOT_SET,
            'required': default_value is REQUIRED,
            'default': None,
            'validators': list(self.default_validators) + (validators or []),
            'dependency': {
                'type': None,  # dependency type:  ref (reference)|exp (expression)|pdg
                'value': None,
                'options': None,
                'enabled': False, # for disable in overrides
            },
            'kwargs': kwargs,

            # ui options
            'description': description,
            'label': label,
            'docs_url': docs_url,
            'widget': widget,
            'order': order,
            'hint': hint,
        }
        self._name: str = kwargs.pop('field_name', '')
        self.__parent_settings = None   # settings class
        self._init_default(default_value)

    def _get_class_config_value(self, name: str, default=None) -> Any:
        return self.__class__._creation_flags.get(name, default)

    def _set_parent_settings(self, settings):
        from ..package_settings import APackageSettings

        if not isinstance(settings, APackageSettings):
            raise ValueError("Parent settings must be an instance of APackageSettings")
        self.__parent_settings = ref(settings)

    def __str__(self):
        return f"{self._data['value']}"

    def __repr__(self):
        return f"<{self.__class__.__name__} [{self.field_type}] ({self._data['value']})>"

    @cached_property
    def type_adapter(self) -> TypeAdapter:
        return TypeAdapter(self.field_type)

    def _init_default(self, default_value: Any):
        if default_value in (REQUIRED, NOT_SET):
            self._data['default'] = None
        else:
            self._data['default'] = default_value
            if default_value is not None:
                self._data['value'] = self._validate(default_value)

    def _validate(self, value: Any) -> Any:
        try:
            v = self.type_adapter.validate_python(value)
        except ValidationError as e:
            raise ValueTypeError(f"Invalid value type: {e}")
        try:
            for validator in self._data['validators']:
                if isinstance(validator, ValidatorBase):
                    v = validator.validate(v)
                elif inspect.isclass(validator) and issubclass(validator, ValidatorBase):
                    v = validator(**self._data['kwargs']).validate(v)
                elif callable(validator) and validator.__module__.startswith('pydantic'):
                    validator(v)
                else:
                    raise TypeError(f"Invalid validator {type(validator)}")
            return v
        except ValidationError as e:
            raise ValueError(f"Validation error: {e}")

    @property
    def settings_instance(self):
        return self.__parent_settings()

    def set_name(self, namespace: str) -> None:
        if not self.__name_pattern.match(namespace):
            raise ValueTypeError(f"Invalid namespace: {namespace}")
        self._name = namespace

    @property
    def name(self):
        return self._name

    @property
    def namespace(self) -> str:
        return self._name.split('.')[0]

    def set(self, value: Any) -> None:
        self._data['value'] = self._validate(value)

    def get(self) -> Any:
        if self._data['value'] is not NOT_SET:
            return self._data['value']
        if not self._data['required']:
            return self._data['default']
        raise ValueError("Field is required but value is not set")

    def get_settings(self):
        result = dict(value=self.get())
        if self._data['dependency']['type'] is not None:
            result['dependency'] = self._data['dependency']
        return result

    def set_dependency(self, dependency_value: dict) -> None:
        self._data['dependency'] = dependency_value

    def set_reference_to(self, parm: Type['BaseField']) -> None:
        if not parm.name:
            raise ValueError("Reference field must have a name")
        self._data['dependency']['value'] = f'ref:{parm.name}'

    def set_comment(self, value: str) -> None:
        self._data['comment'] = TypeAdapter(str).validate_python(value)

    def get_comment(self) -> str:
        return self._data['comment']

    def is_required(self) -> bool:
        return self._data['required']

    def has_value(self) -> bool:
        return self._data['value'] is not NOT_SET or (not self._data['required'] and self._data['default'] is not None)

    def get_serialized(self) -> Any:
        value = self.get()
        return self._serialize_value(value)

    def _serialize_value(self, value: Any) -> Any:
        if value is None:
            return None
        if isinstance(value, BaseModel):
            return value.model_dump()
        if isinstance(value, (list, tuple)):
            return [self._serialize_value(item) for item in value]
        if isinstance(value, dict):
            return {str(k): self._serialize_value(v) for k, v in value.items()}
        return value

    def get_schema(self) -> dict:
        schema = {
            'field_type': to_js_type(self.field_type),
            'field_name': self.__class__.__name__,
            'required': self.is_required(),
            'default': self._serialize_value(self._data['default']),
            'validators': self._get_validators_schema(),
            'dependency': self._data['dependency'],
            **self.get_additional_info()
        }
        if self._data['description']:
            schema['description'] = self._data['description']
        return schema

    def get_additional_info(self) -> dict:
        return {
            'label': self._data.get('label') or unslugify(self.name),
            'widget': self._data['widget'],
            'docs_url': self._data['docs_url'],
            'description': self._data['description'],
            'hint': self._data['hint'],
        }

    def _get_validators_schema(self) -> list[dict]:
        validators_schema = []
        for validator in self._data['validators']:
            if isinstance(validator, ValidatorBase):
                validators_schema.append({
                    'name': validator.name,
                    'params': {k: v for k, v in validator.options.items() if v is not None},
                })
            elif inspect.isclass(validator) and issubclass(validator, ValidatorBase):
                validators_schema.append({
                    'name': validator.name,
                    # 'params': self._data['kwargs']
                })
            elif hasattr(validator, '__name__'):  # Pydantic validators
                validators_schema.append({
                    'name': validator.__name__,
                    'params': {}
                })
        return validators_schema
