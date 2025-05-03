from typing import Any, Type, Optional

from pydantic import BaseModel
from pydantic_core import ValidationError

from agio.core.settings.fields.base_field import BaseField
from agio.core.settings.generic_types import REQUIRED


class ModelField(BaseField):
    def __init__(self, default_value: Any = REQUIRED, model: Type[BaseModel] = None):
        self.model = model
        super().__init__(default_value)

    def _validate(self, value: Any) -> Any:
        if value is None:
            return None

        if self.model is None:
            raise ValueError("Model must be specified for ModelField")

        if isinstance(value, self.model):
            return value

        try:
            return self.model.model_validate(value)
        except ValidationError as e:
            raise ValueError(f"Model validation failed: {e}")

    def get_serialized(self) -> Optional[dict]:
        value = self.get()
        if value is None:
            return None
        return value.model_dump()
