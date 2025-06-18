from datetime import datetime
from typing import TypeVar, Union, Type, Callable


REQUIRED = type('REQUIRED', (object,), {
    '__repr__': lambda self, *args, **kwargs: '<REQUIRED>',
    '__str__': lambda self, *args, **kwargs: '<REQUIRED>',
    '__bool__': lambda self, *args, **kwargs: False})

NOT_SET = type('NOT_SET', (object,), {
    '__repr__': lambda self, *args, **kwargs: '<NOT_SET>',
    '__str__': lambda self, *args, **kwargs: '<NOT_SET>',
    '__bool__': lambda self, *args, **kwargs: False})

ComparableType = TypeVar('ComparableType', int, float, datetime, str)


class SettingsType:
    LOCAL = 'local'
    WORKSPACE = 'workspace'
