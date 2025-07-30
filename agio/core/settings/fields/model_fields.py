import inspect
from typing import Any, Type, Optional

from pydantic import BaseModel
from pydantic_core import ValidationError

from agio.core.settings.fields.base_field import BaseField
from agio.core.settings.generic_types import REQUIRED


class ModelField(BaseField):
    def __init__(self, default_value: Any = REQUIRED, model: Type[BaseModel] = None):
        from agio.core.settings.package_settings import _iterate_pydantic_type_hints

        if not model or not (inspect.isclass(model) and issubclass(model, BaseModel)):
            raise ValueError("ModelField must be initialized with a Pydantic BaseModel class.")
        self.model = model
        self.field_type = model # Устанавливаем field_type в класс модели
        super().__init__(default_value)
        # Генерируем и сохраняем Pydantic схему при инициализации
        # _iterate_pydantic_type_hints будет вызываться здесь для проверки
        # вложенных полей Pydantic модели на наличие BaseField
        list(iter(_iterate_pydantic_type_hints(self.model))) # Принудительно запускаем итерацию для проверки
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
        # Переопределяем field_type и field_name в соответствии с требованиями
        schema['field_type'] = "object" # Pydantic model is an object in JSON schema
        schema['field_name'] = "ModelField"
        # Добавляем полную Pydantic схему модели
        schema['schema'] = self._pydantic_schema
        return schema
