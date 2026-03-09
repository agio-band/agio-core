import inspect
import sys
from collections import defaultdict
from typing import Any, Generator

from agio.core.events import emit


class ChipLoadingError(Exception):
    pass


class ChipHub:
    def __init__(self):
        self._collections = defaultdict(list)

    @property
    def collections(self):
        return self._collections

    def add_chip(self, chip_class: Any, collection_name: str, chip_name: str = None):
        if not inspect.isclass(chip_class):
            raise TypeError('Object is not a class')
        chip_class.package_name = self._get_package_name(chip_class)
        chip_class._is_chip = True
        if chip_name:
            setattr(chip_class, 'chip_name', chip_name)
        else:
            # if inherited from other chip
            if hasattr(chip_class, 'chip_name'):
                delattr(chip_class, 'chip_name')
        if chip_class in self._collections[collection_name]:
            raise ChipLoadingError(f'Chip {chip_class} already loaded')
        emit('core.chips.before_add', {'cls': chip_class, 'collection': collection_name})
        self._collections[collection_name].append(chip_class)
        emit('core.chips.added', {'cls': chip_class, 'collection': collection_name})

    def get_collection(self, collection_name: str) -> tuple:
        if collection_name not in self._collections:
            raise NameError(f'chips collection {collection_name} not found')
        return tuple(self._collections[collection_name])

    def iter_chips(self, collection_name: str) -> Generator[tuple, None, None]:
        yield from self._collections[collection_name]

    @staticmethod
    def _get_package_name(cls):
        module_name = cls.__module__
        module = sys.modules.get(module_name)
        package_name = getattr(module, '__name__', module_name)
        return package_name

    @staticmethod
    def is_chip(obj: Any) -> bool:
        return getattr(obj, '_is_chip', False)

    @staticmethod
    def get_chip_name(obj: Any) -> str:
        return getattr(obj, 'chip_name', getattr(obj, '__name__', getattr(obj, '__qualname__', repr(obj))))

    def find_chip(self, collection_name: str, chip_name: str) -> object|None:
        if collection_name not in self._collections:
            raise NameError(f'chips collection {collection_name} not found')
        for chip in self._collections[collection_name]:
            if self.get_chip_name(chip) == chip_name:
                return chip
        return None
