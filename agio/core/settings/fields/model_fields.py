import inspect
from typing import Any, Type, Optional

from pydantic import BaseModel
from pydantic_core import ValidationError

from agio.core.settings.fields.base_field import BaseField
from agio.core.settings.generic_types import REQUIRED


class ModelField(BaseField):
    def __init__(self, default: Any = REQUIRED, model: Type[BaseModel] = None):
        from agio.core.settings.package_settings import _iterate_pydantic_type_hints

        if not model or not (inspect.isclass(model) and issubclass(model, BaseModel)):
            raise ValueError("ModelField must be initialized with a Pydantic BaseModel class.")
        self.model = model
        self.field_type = model
        super().__init__(default)
        list(iter(_iterate_pydantic_type_hints(self.model)))
        self._pydantic_schema = self.model.model_json_schema()

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
            raise ValueError(f"Model validation for field '{self._name}' failed: {e}")

    def get_serialized(self) -> Optional[dict]:
        value = self.get()
        if value is None:
            return None
        return value.model_dump()

    def get_schema(self) -> dict:
        schema = super().get_schema()
        schema['field_type'] = "model"
        # schema['field_name'] = "ModelField"
        schema['type_schema'] = self._pydantic_schema
        return schema
