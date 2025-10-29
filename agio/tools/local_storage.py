"""
Хранение локальных данных с помощью diskcache
"""
import json
from pathlib import Path
from typing import Any

import diskcache


class LocalStorage:
    _NOT_EXISTS = object()

    def __init__(self, store_path: str|Path):
        self.path = Path(store_path)
        self._cache = None

    @property
    def db(self):
        if self._cache is None:
            self.path.mkdir(parents=True, exist_ok=True)
            self._cache = diskcache.Cache(self.path.as_posix())
        return self._cache

    def get(self, key, default=None):
        value = self.db.get(key, default=self._NOT_EXISTS)
        if value is not self._NOT_EXISTS:
            value = json.loads(value.decode())
        else:
            value = default
        return value

    def set(self, key: str, value: Any):
        data = json.dumps(value, ensure_ascii=False).encode('utf-8', errors="ignore")
        self.db.set(key, data)

    def delete(self, key):
        return self.db.delete(key)

    def keys(self):
        return tuple(self._cache.iterkeys())

    def clear(self):
        self.db.clear()
