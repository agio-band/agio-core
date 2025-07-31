from datetime import datetime
from functools import cached_property
from numbers import Real
from pathlib import Path
from typing import Any, Union, get_args, TypeVar

from pydantic import EmailStr, AnyUrl

from agio.core.settings.fields.base_field import BaseField
from agio.core.settings.fields.generic_fields import StringField
from agio.core.settings.fields.compaund_fields import ListField
from agio.core.settings.validators import RegexValidator


class DateTimeField(BaseField):
    field_type = datetime

    def _validate(self, value: Any) -> Any:
        if isinstance(value, str):
            try:
                value = datetime.fromisoformat(value)
            except ValueError as e:
                raise ValueError(f"Invalid datetime string: {value}") from e
        elif isinstance(value, datetime):
            return super()._validate(value)
        raise ValueError(f"Expected datetime or ISO string, got {type(value)}")

    def get_serialized(self) -> Any:
        value = self.get()
        return value.isoformat() if value is not None else None


class EmailField(StringField):
    default_validators = [EmailStr]


class UrlField(StringField):
    default_validators = [AnyUrl]


class FrameRangeField(ListField[int]):
    field_type = tuple[int, ...]
    default_validators = []

    def _validate(self, value: Any) -> tuple[int, ...]:
        if isinstance(value, tuple):
            value = list(value)

        if len(value) not in (2, 3):
            raise ValueError("Frame range must have exactly 2 or 3 elements")
        value_list = list(super()._validate(value[:2]))

        start, end = value_list[:2]
        step = value[2] if len(value) == 3 else 1
        if not isinstance(step, int):
            raise ValueError(f"Frame step must be of type int, got {type(step)}")

        if start > end:
            raise ValueError(f"Start frame {start} cannot be greater than end frame {end}")

        return start, end, step

    @property
    def first_frame(self):
        return self.get()[0]

    @property
    def last_frame(self):
        return self.get()[1]

    @property
    def step(self):
        return self.get()[2]

    @property
    def frame_count(self):
        return (self.last_frame - self.first_frame) // self.step + 1


class VectorField(ListField[float]):
    field_type = tuple[float, ...]
    element_count = None

    def _validate(self, value: Any) -> tuple[float, ...]:
        if isinstance(value, tuple):
            value = list(value)

        value_list = tuple(super()._validate(value))

        if self.element_count and len(value_list) != self.element_count:
            raise ValueError(f"Vector must have exactly {self.element_count} elements")
        return value_list


class Vector2Field(VectorField):
    element_count = 2

    @property
    def x(self):
        return self.get()[0]
    @property
    def y(self):
        return self.get()[1]


class Vector3Field(Vector2Field):
    element_count = 3
    @property
    def z(self):
        return self.get()[2]


class Vector4Field(Vector3Field):
    element_count = 4

    @property
    def w(self):
        return self.get()[3]


ColorRGBType = tuple[int, int, int]
ColorRGBAType = tuple[int, int, int, int]
ColorInputType = Union[str, tuple[Real, ...], list[Real]]
ColorType = TypeVar('ColorType', bound=tuple[int, ...]) # A generic type for color tuples


class _BaseColorField(BaseField[ColorType]):
    """
    A base class for color fields, providing unified set/get logic
    for RGB and RGBA.
    """
    field_type: type[ColorType] # To be defined by subclasses (e.g., ColorRGBType, ColorRGBAType)
    component_names: list[str] = [] # To be defined by subclasses

    @cached_property
    def _element_count(self) -> int:
        """Dynamically determines the number of color components based on field_type."""
        return len(get_args(self.field_type))

    def set(self, value: ColorInputType) -> None:
        """
        Sets the color value.
        Accepts HEX strings or tuples/lists with the appropriate number of components.
        """
        if isinstance(value, str):
            # Hex always produces RGB, so we need to ensure it matches the expected count
            rgb_components = self._hex_to_rgb(value)
            if self._element_count == 3:
                validated = self._validate_components(*rgb_components)
            elif self._element_count == 4:
                # If RGBA, default alpha to 255 (or 1.0) when setting from hex
                validated = self._validate_components(*rgb_components, 255)
            else:
                raise ValueError("Unsupported color type for hex conversion.")
        elif isinstance(value, (tuple, list)):
            if len(value) == self._element_count:
                validated = self._validate_components(*value)
            else:
                raise ValueError(
                    f"Color must have {self._element_count} components, got {len(value)}"
                )
        else:
            raise ValueError(f"Unsupported color format: {type(value)}")

        super().set(self.field_type(validated)) # Cast to the specific tuple type

    def get(self, as_hex: bool = False, as_float: bool = False) -> Union[str, ColorType, tuple[float, ...]]:
        """
        Gets the color value in various formats.
        :param as_hex: If True, returns color as a HEX string.
        :param as_float: If True, returns color components as floats (0.0-1.0).
        """
        current_value = super().get()

        if as_hex:
            # Only 3 components can be represented as hex. If RGBA, we just take RGB.
            if len(current_value) >= 3:
                r, g, b = current_value[0], current_value[1], current_value[2]
                return f"#{r:02x}{g:02x}{b:02x}"
            else:
                raise ValueError("Cannot convert to HEX: color type does not have RGB components.")
        elif as_float:
            return tuple(comp / 255.0 for comp in current_value)
        else:
            return current_value

    def _validate_components(self, *values: Real) -> tuple[int, ...]:
        """
        Validates and normalizes color components.
        Handles both 0-255 and 0.0-1.0 ranges.
        """
        validated = []
        for i, value in enumerate(values):
            name = self.component_names[i] if i < len(self.component_names) else f"Component {i+1}"
            if not isinstance(value, Real):
                raise ValueError(f"{name} must be a number, got {type(value)}")

            value_float = float(value)
            if 0.0 <= value_float <= 1.0:
                validated.append(int(value_float * 255))
            elif 0.0 <= value_float <= 255.0:
                validated.append(int(value_float))
            else:
                raise ValueError(f"{name} value {value} out of range (0-255 or 0.0-1.0)")
        return tuple(validated)

    @staticmethod
    def _hex_to_rgb(hex_str: str) -> ColorRGBType:
        """Converts a HEX string (#RGB or #RRGGBB) to an RGB tuple (0-255)."""
        hex_str = hex_str.strip().lstrip('#')
        if not all(c in '0123456789abcdefABCDEF' for c in hex_str):
            raise ValueError("HEX string contains invalid characters")
        if len(hex_str) == 3:
            hex_str = ''.join([c * 2 for c in hex_str])
        elif len(hex_str) != 6:
            raise ValueError("Invalid HEX format. Expected #RGB or #RRGGBB")

        return (
            int(hex_str[0:2], 16),
            int(hex_str[2:4], 16),
            int(hex_str[4:6], 16)
        )


class RGBColorField(_BaseColorField[ColorRGBType]):
    field_type = ColorRGBType
    component_names = ["red", "green", "blue"]


class RGBAColorField(_BaseColorField[ColorRGBAType]):
    field_type = ColorRGBAType
    component_names = ["red", "green", "blue", "alpha"]


class PathField(BaseField):
    field_type = str


class DirectoryField(BaseField):
    field_type = str


class SlugField(StringField):
    default_validators = (
        RegexValidator(pattern=r'^[a-z][a-z0-9_]+$'),
    )