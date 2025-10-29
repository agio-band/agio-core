from datetime import datetime
from typing import TypeVar

from agio.tools.singleton import Singleton


class __Constant(metaclass=Singleton):
    pass

REQUIRED = type('REQUIRED', (__Constant,), {
    '__repr__': lambda self, *args, **kwargs: '<REQUIRED>',
    '__str__': lambda self, *args, **kwargs: '<REQUIRED>',
    '__bool__': lambda self, *args, **kwargs: True,
})()


NOT_SET = type('NOT_SET', (__Constant,), {
    '__repr__': lambda self, *args, **kwargs: '<NOT_SET>',
    '__str__': lambda self, *args, **kwargs: '<NOT_SET>',
    '__bool__': lambda self, *args, **kwargs: False,
    '__eq__': lambda self, other: isinstance(other , type(NOT_SET)),
})()


ComparableType = TypeVar('ComparableType', int, float, datetime, str)


class SettingsType:
    LOCAL = 'local'
    WORKSPACE = 'workspace'

