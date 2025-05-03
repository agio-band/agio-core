from datetime import datetime
from numbers import Real
from typing import Any, Union

from pydantic import EmailStr, AnyUrl

from agio.core.settings.fields.base_field import BaseField
from agio.core.settings.fields.generic_fields import StringField
from agio.core.settings.fields.compaund_fields import ListField



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

        value_list = super()._validate(value)

        if self.element_count and len(value_list) != self.element_count:
            raise ValueError(f"Vector must have exactly {self.element_count} elements")
        return tuple(value_list)


class Vector2Field(VectorField):
    element_count = 2


class Vector3Field(VectorField):
    element_count = 3


class Vector4Field(VectorField):
    element_count = 4


ColorRGB = tuple[int, int, int]
ColorRGBA = tuple[int, int, int, int]
ColorInput = Union[str, tuple[Real, ...], list[Real]]


class ColorField(BaseField):
    field_type = ColorRGB  # Всегда храним как RGB tuple[int, int, int]

    def set(self, value: ColorInput) -> None:
        """Автоматически определяет формат и вызывает соответствующий метод"""
        if isinstance(value, str):
            self.set_hex(value)
        elif isinstance(value, (tuple, list)):
            if len(value) == 4:
                self.set_rgba(*value)
            elif len(value) == 3:
                self.set_rgb(*value)
            else:
                raise ValueError("Color must have 3 (RGB) or 4 (RGBA) components")
        else:
            raise ValueError(f"Unsupported color format: {type(value)}")

    def set_hex(self, hex_str: str) -> None:
        """Установка цвета из HEX строки (#RGB, #RRGGBB)"""
        hex_str = hex_str.strip().lower()
        if not (hex_str.startswith('#') and len(hex_str) in (4, 7)):
            raise ValueError("Invalid HEX format. Expected #RGB or #RRGGBB")

        hex_part = hex_str[1:]
        if not all(c in '0123456789abcdef' for c in hex_part):
            raise ValueError("HEX string contains invalid characters")

        # Конвертируем в RGB и сохраняем
        rgb = self._hex_to_rgb(hex_str)
        super().set(rgb)

    def set_rgb(self, r: Real, g: Real, b: Real) -> None:
        """Установка цвета из RGB компонентов (0-255 или 0.0-1.0)"""
        validated = (
            self._validate_component(r, 'Red'),
            self._validate_component(g, 'Green'),
            self._validate_component(b, 'Blue')
        )
        super().set(validated)

    def set_rgba(self, r: Real, g: Real, b: Real, a: Real) -> None:
        """Установка цвета из RGBA компонентов (альфа игнорируется)"""
        self.set_rgb(r, g, b)  # Просто используем RGB компоненты

    def _validate_component(self, value: Real, name: str = 'Component') -> int:
        """Проверяет и нормализует цветовой компонент"""
        if not isinstance(value, Real):
            raise ValueError(f"{name} must be a number, got {type(value)}")

        value_float = float(value)
        if 0.0 <= value_float <= 1.0:
            return int(value_float * 255)
        elif 0.0 <= value_float <= 255.0:
            return int(value_float)
        else:
            raise ValueError(f"{name} value {value} out of range (0-255 or 0.0-1.0)")

    @staticmethod
    def _hex_to_rgb(hex_str: str) -> ColorRGB:
        """Конвертирует HEX строку в RGB tuple"""
        hex_str = hex_str.lstrip('#')
        if len(hex_str) == 3:
            hex_str = ''.join([c * 2 for c in hex_str])
        return (
            int(hex_str[0:2], 16),
            int(hex_str[2:4], 16),
            int(hex_str[4:6], 16)
        )

    # Методы get остаются без изменений
    def get_hex(self) -> str:
        r, g, b = self.get()
        return f"#{r:02x}{g:02x}{b:02x}"

    def get_rgb(self) -> ColorRGB:
        return self.get()

    def get_rgba(self, alpha: int = 255) -> ColorRGBA:
        r, g, b = self.get()
        return (r, g, b, alpha)

    def get_rgb_float(self) -> tuple[float, float, float]:
        r, g, b = self.get()
        return r / 255.0, g / 255.0, b / 255.0

    def get_rgba_float(self, alpha: float = 1.0) -> tuple[float, float, float, float]:
        r, g, b = self.get_rgb_float()
        return (r, g, b, alpha)

