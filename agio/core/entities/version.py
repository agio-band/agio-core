import os
from pathlib import Path
from typing import Self, Iterator
from uuid import UUID

from agio.core import api
from agio.core.entities import BaseObject, product
from agio.core.entities import task
from agio_pipe.schemas.version import AVersionCreateSchema
from agio_pipe.utils import template_solver


class AVersion(BaseObject):
    object_name = "version"

    VERSION_PADDING = os.getenv('AGIO_VERSION_NUMBER_PADDING', 7)

    @property
    def version_number(self):
        return int(self._data['name'])

    def get_product(self):
        return product.AProduct(self.data['publish']['id'])

    @classmethod
    def get_data(cls, object_id: str, client=None) -> dict:
        return api.pipe.get_version(object_id, client=client)

    def update(self, fields: dict, dependencies: list[str] = None) -> None:
        return api.pipe.update_version(self.id, fields, dependencies=dependencies, client=self.client)

    @classmethod
    def iter(cls, product_id: str|UUID, client=None) -> Iterator[Self]:
        for data in api.pipe.iter_prodict_versions(product_id, client=client):
            yield AVersion(data, client=client)

    @classmethod
    def get_next_version_number(cls, product_id: str, client=None) -> int:
        return api.pipe.get_next_version_number(product_id, client=client)

    @classmethod
    def create(cls,
               product_id: str|UUID,
               task_id: str|UUID,
               publish_session_id: str|UUID,
               version: int = None,
               fields: dict = None,
               client=None,
        ) -> Self:
        if version is None:
            version = cls.get_next_version_number(product_id, client=client)
        # add padding
        version = f"{version:0{cls.VERSION_PADDING}d}"
        schema = AVersionCreateSchema(
            **dict(
                product_id=product_id,
                task_id=task_id,
                publish_session_id=publish_session_id,
                version=version,
                fields=fields
            ),
        )
        version_id = api.pipe.create_version(**schema.model_dump(), client=client)
        return AVersion(version_id, client=client)

    def delete(self) -> bool:
        return api.pipe.delete_version(self.id, client=self.client)

    @classmethod
    def find(cls, **kwargs):
        raise NotImplementedError()

    def get_task(self) -> task.ATask:
        data = task.ATask.get_data(self._data['entity']['id'])
        return task.ATask(data)

    def to_dict(self):
        return dict(
            id=self.id,
            entity=self._data['entity'],
            fields=self._data['fields'],
            name=self._data['name'], # for deserialize
            version=self.version_number,
            product=self.get_product().to_dict(),
        )

    def __get_context(self):
        from agio.core.settings import get_local_settings
        project = self.get_task().project
        local_settings = get_local_settings(project=project)
        context = dict(
            local_roots={k.name: k.path for k in local_settings.get('agio_pipe.local_roots')},
            project=project,
        )
        return context

    def iter_files_with_local_path(self) -> Iterator[Path]|None:
        files = self.fields['published_files']
        if files:
            project = self.get_task().project
            ws_settings = project.get_settings()
            templates = ws_settings.get('agio_pipe.publish_templates')
            if templates is None:
                raise RuntimeError('No agio publish templates configured')
            templates = {tmpl.name: tmpl.pattern for tmpl in templates}
            context = self.__get_context()
            solver = template_solver.TemplateSolver(templates)
            project_root = solver.solve('project', context)
            for file in files:
                yield Path(project_root) / file['relative_path']
