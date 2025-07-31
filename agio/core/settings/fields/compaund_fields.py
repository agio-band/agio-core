from typing import Generic, Any, Type, Iterable, Collection, Union, Sized, TypeVar

from pydantic import TypeAdapter
from pydantic_core import ValidationError

from agio.core.settings.fields.base_field import BaseField
from agio.core.settings.fields.js_types import to_js_type
from agio.core.settings.generic_types import REQUIRED


T = TypeVar('T')
K = TypeVar('K')
V = TypeVar('V')
D = TypeVar('D')


class CollectionField(BaseField[list[T]]):
    # _element_type: Type[T] | None = None
    def __init__(self, default_value: Any = REQUIRED, **kwargs):
        self._element_type: Type[T] | None = None
        super().__init__(default_value, **kwargs)

    @property
    def element_type(self) -> Type[T] | None:
        return self._element_type

    @element_type.setter
    def element_type(self, value: Type[T]):
        self._element_type = value

    def _convert_input(self, value: Any) -> Iterable | None:
        if value is None:
            return None
        if not isinstance(value, Iterable) or isinstance(value, (str, bytes)):
            raise ValueError(f"Expected iterable (not string), got {type(value)}")
        return value

    def _validate_elements(self, iterable: Iterable) -> Iterable[T] | None:
        if iterable is None:
            return None
        return type(iterable)(self._validate_element(item) for item in iterable)

    def _validate_element(self, element: Any) -> T:
        if self.element_type is None:
            return element
        return TypeAdapter(self.element_type).validate_python(element)

    def _validate(self, value: Any) -> Iterable[T]:
        try:
            iterable = self._convert_input(value)
            return self._validate_elements(iterable)
        except ValidationError as e:
            raise ValueError(f"Element validation failed: {e}")

    def get_additional_info(self):
        info = super().get_additional_info()
        compound_info = to_js_type(self._element_type)
        info['element_type'] = compound_info['field_type']
        info['element_type_schema'] = compound_info.get('type_schema')
        return info

class ListField(CollectionField[T]):
    field_type = list[T]


class SetField(CollectionField[T]):
    field_type = set[T]

    def _validate_elements(self, iterable: Iterable) -> set[T] | None:
        if iterable is None:
            return
        return set(self._validate_element(item) for item in iterable)


class TupleField(CollectionField[T]):
    field_type = tuple[T, ...]
    _element_types: tuple[Type, ...] | None = None

    @property
    def element_types(self) -> tuple[Type, ...] | None:
        return self._element_types

    @element_types.setter
    def element_types(self, value: tuple[Type, ...]):
        self._element_types = value

    def _validate_elements(self, iterable: Union[Iterable, Sized]) -> tuple | None:
        if iterable is None:
            return
        iterable = self.type_adapter.validate_python(iterable)
        if self.element_types:
            if len(self.element_types) == 2 and self.element_types[1] is ...:
                element_type = self.element_types[0]
                if not all(isinstance(x, element_type) for x in iterable):
                    raise ValueError(f"All elements must be of type {element_type}")
            else:
                if len(iterable) != len(self.element_types):
                    raise ValueError(f"Expected tuple of length {len(self.element_types)}, got {len(iterable)}")
                for i, (val, typ) in enumerate(zip(iterable, self.element_types)):
                    if not isinstance(val, typ):
                        raise ValueError(f"Element {i} must be of type {typ}, got {type(val)}")
        return iterable


class DictField(BaseField, Generic[K, V]):
    field_type = dict[K, V]
    _key_type = None
    _value_type = None

    def _resolve_types(self):
        if self._key_type is None or self._value_type is None:
            for base in getattr(self.__class__, '__orig_bases__', []):
                if hasattr(base, '__args__') and len(base.__args__) == 2:
                    self._key_type, self._value_type = base.__args__
                    break

    @property
    def key_type(self):
        self._resolve_types()
        return self._key_type

    @property
    def value_type(self):
        self._resolve_types()
        return self._value_type

    def _validate(self, value: Any) -> Any:
        if value is None:
            return None

        if not isinstance(value, dict):
            raise ValueError(f"Expected dict, got {type(value)}")

        self._resolve_types()

        if self.key_type is not None and self.value_type is not None:
            try:
                return {
                    TypeAdapter(self.key_type).validate_python(k):
                        TypeAdapter(self.value_type).validate_python(v)
                    for k, v in value.items()
                }
            except ValidationError as e:
                raise ValueError(f"Dict validation failed: {e}")

        return value


class TableField(BaseField, Generic[D]):    # TODO
    field_type = list[list[D, ...]]
