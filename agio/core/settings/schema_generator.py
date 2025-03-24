from pprint import pprint
from pydantic import BaseModel, Field
from pydantic.json_schema import GenerateJsonSchema, JsonSchemaValue
from typing import Any, Dict, ClassVar, get_type_hints
from pydantic_core import core_schema


class SchemaGeneratorWithOptions(GenerateJsonSchema):
    def model_schema(self, schema: core_schema.ModelSchema) -> JsonSchemaValue:
        """Generates a JSON schema that matches a schema that defines a model."""
        cls = schema['cls']
        config = cls.model_config

        with self._config_wrapper_stack.push(config):
            json_schema = self.generate_inner(schema['schema'])

        self._update_class_schema(json_schema, cls, config)

        custom_fields = self.extract_custom_fields(cls)

        if custom_fields:
            json_schema["options"] = custom_fields

        return json_schema

    def extract_custom_fields(self, cls: type[BaseModel]) -> Dict[str, Any]:
        custom_fields = {}
        if hasattr(cls, 'Options'):
            custom_fields_class = getattr(cls, 'Options')
            type_hints = get_type_hints(custom_fields_class)
            for name, value in custom_fields_class.__dict__.items():
                print(name)
                if not name.startswith('__') and not callable(value):
                    custom_fields[name] = value
        return custom_fields
