import inspect
from abc import ABC
from functools import cached_property
from typing import Any, Callable, Type, Union

from pydantic import TypeAdapter, BaseModel
from pydantic_core import ValidationError

from agio.core.settings.exceptions import ValueTypeError
from agio.core.settings.generic_types import REQUIRED, NOT_SET
from agio.core.settings.validators import ValidatorBase


ValidatorType = Union[Type[ValidatorBase], ValidatorBase, Callable]


class BaseField(ABC):
    field_type: Any = None
    default_validators: list[ValidatorType] = []

    def __init__(
        self,
        default_value: Any = REQUIRED,
        validators: list[ValidatorType] = None,
        help_text: str = None,
        **kwargs
    ):
        self._data: dict[str, Any] = {
            'value': NOT_SET,
            'required': default_value is REQUIRED,
            'default': None,
            'validators': list(self.default_validators) + (validators or []),
            'kwargs': kwargs,
            'help_text': help_text,
        }
        self._init_default(default_value)

    def __str__(self):
        return f"{self._data['value']}>"

    def __repr__(self):
        return f"<{self.__class__.__name__}: {self.field_type}:{self._data['value']}>"

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

    def set(self, value: Any) -> None:
        self._data['value'] = self._validate(value)

    def get(self) -> Any:
        if self._data['value'] is not NOT_SET:
            return self._data['value']
        if not self._data['required']:
            return self._data['default']
        raise ValueError("Field is required but value is not set")

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
        """Возвращает схему поля"""
        schema = {
            'type': self.field_type.__name__,
            'type_str': str(self.field_type),
            'required': self.is_required(),
            'default': self._serialize_value(self._data['default']),
            'validators': self._get_validators_schema(),
        }

        if self._data['help_text']:
            schema['help_text'] = self._data['help_text']

        return schema

    def _get_validators_schema(self) -> list[dict]:
        """Возвращает схему валидаторов"""
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
            elif hasattr(validator, '__name__'):  # Pydantic валидаторы
                validators_schema.append({
                    'name': validator.__name__,
                    'params': {}
                })
        return validators_schema
