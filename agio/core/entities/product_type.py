from __future__ import annotations

import os
from typing import Iterator
from uuid import UUID

from agio.core import api
from agio.core.entities import BaseObject


class AProductType(BaseObject):
    object_name = "product_type"

    @classmethod
    def get_data(cls, object_id: str | UUID) -> dict:
        return api.pipe.get_product_type(object_id)

    def update(self, config: dict = None, data_type: str = None) -> None:
        return api.pipe.update_product_type(
            self.id,
            config=config,
            data_type=data_type,
        )

    def set_config(self, config: dict) -> None:
        return self.update(config=config)

    def __get_config_from_file(self) -> dict|None:
        from agio.tools import modules
        func_name = os.getenv('AGIO_GET_PRODUCT_CONFIG_FUNC')
        if func_name:
            func = modules.import_object_by_dotted_path(func_name)
            return func(self.name)
        return None

    def get_config(self) -> dict:
        from_file = self.__get_config_from_file()
        if from_file:
            return from_file
        if 'config' not in self._data:
            self.reload()
        return self._data.get("config", {})

    @classmethod
    def iter(cls, **kwargs) -> Iterator[AProductType]:
        for prod in api.pipe.iter_product_types(**kwargs):
            yield cls(prod)

    @classmethod
    def create(cls,
               name: str,
               description: str,
               config: dict = None,
               data_type: str = None,
               ) -> AProductType:
        product_type_id = api.pipe.create_product_type(
            name, description, config, data_type)
        return cls(product_type_id)

    def delete(self) -> None:
        raise NotImplementedError

    @classmethod
    def find(cls,
             name: str,
             **kwargs):
        data = api.pipe.get_product_type_by_name(name)
        if not data:
            return
        return cls(data)

    @property
    def name(self) -> str:
        return self._data["name"]

    @property
    def data_type(self) -> str:
        return self._data["dataType"]






