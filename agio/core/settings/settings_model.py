from typing import Any
from .schema_generator import SchemaGeneratorWithOptions
from pydantic import BaseModel
from pydantic.json_schema import DEFAULT_REF_TEMPLATE, GenerateJsonSchema, JsonSchemaMode


class ASettingsModel(BaseModel):
    @classmethod
    def model_json_schema(
            cls,
            by_alias: bool = True,
            ref_template: str = DEFAULT_REF_TEMPLATE,
            schema_generator: type[GenerateJsonSchema] | None = None,
            mode: JsonSchemaMode = 'validation',
    ) -> dict[str, Any]:
        generator = schema_generator or SchemaGeneratorWithOptions
        return super().model_json_schema(
            by_alias=by_alias,
            ref_template=ref_template,
            schema_generator=generator,
            mode=mode
        )

