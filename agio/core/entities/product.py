from __future__ import annotations

import re
from typing import Iterator
from uuid import UUID

from agio.core import api
from agio.core.entities import BaseObject, AEntity, product_type


class AProduct(BaseObject):
    object_name = "product"

    @classmethod
    def get_data(cls, object_id: str | UUID, client=None) -> dict:
        return api.pipe.get_product(object_id, client=client)

    def update(self, name: str = None, variant: str = None, fields: dict = None, **kwargs) -> None:
        return api.pipe.update_product(
            self.id,
            name=name,
            variant=variant,
            fields=fields,
            client=self.client,
        )

    @classmethod
    def iter(cls,
             entity: str | UUID | AEntity,
             product_type_id: str = None,
             product_type_name: str = None,
             client=None,
             **kwargs) -> Iterator['AProduct']:
        if isinstance(entity, AEntity):
            entity = str(entity.id)
        for prod in api.pipe.iter_products(
                entity_id=entity,
                product_type_id=product_type_id,
                product_type_name=product_type_name,
                client=client,
            ):
            yield cls(prod, client=client)

    @classmethod
    def create(cls,
               entity_id: str | UUID,
               name: str,
               product_type_id: str,
               variant: str,
               fields: dict = None,
               client=None,
               ) -> 'AProduct':
        product_id = api.pipe.create_product(name, entity_id, variant, product_type_id=product_type_id, fields=fields, client=client)
        return cls(product_id, client=client)

    def delete(self) -> None:
        raise NotImplementedError

    @classmethod
    def find(cls,
             entity_id: str | UUID,
             name: str,
             variant: str = None,
             client=None,
             **kwargs) -> AProduct|None:
        data = api.pipe.find_product(entity_id=entity_id, name=name, variant=variant, client=client)
        if data:
            return cls(data, client=client)
        return None

    @property
    def name(self) -> str:
        return self._data["name"]

    @property
    def variant(self) -> str:
        return self._data["variant"]

    @property
    def type(self) -> product_type.AProductType:
        return product_type.AProductType(self._data["type"])

    @property
    def entity(self) -> AEntity:
        entity_data = api.track.get_entity(self._data["entityId"], client=self.client)
        return AEntity.from_data(entity_data)

    VALID_VARIANT_PATTERN = re.compile(r'^[a-z](?:[a-z0-9_]*[a-z0-9])?$')

    @classmethod
    def validate_variant_name(cls, name: str) -> bool:
        return bool(cls.VALID_VARIANT_PATTERN.match(name))




