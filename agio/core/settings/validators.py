import re
from abc import ABC, abstractmethod
from datetime import datetime
from numbers import Number
from typing import Generic, Collection

from agio.core.settings.generic_types import ComparableType



class ValidatorBase(ABC):
    name: str = None

    def __init__(self, **kwargs):
        self.options: dict = kwargs

    @abstractmethod
    def validate(self, value):
        pass

    def __repr__(self):
        return f"<Validator: {self.name} {self.options}>"


class LengthLimitValidator(ValidatorBase):
    name = "length-limit"

    def __init__(self, min_length: int = None, max_length: int = None): # TODO replace with stubs
        super().__init__(min_length=min_length, max_length=max_length)

    def validate(self, value):
        if not isinstance(value, (str, list, dict)):
            raise ValueError(f"Length validation not applicable for {type(value)}")

        length = len(value)
        if self.options['min_length'] is not None and length < self.options['min_length']:
            raise ValueError(f"Length {length} < min_length {self.options['min_length']}")
        if self.options['max_length'] is not None and length > self.options['max_length']:
            raise ValueError(f"Length {length} > max_length {self.options['max_length']}")
        return value


class RangeLimitValidator(ValidatorBase, Generic[ComparableType]):
    name = "range-limit"

    def __init__(
        self,
        ge: ComparableType = None,
        le: ComparableType = None,
        gt: ComparableType = None,
        lt: ComparableType = None
    ):
        super().__init__(ge=ge, le=le, gt=gt, lt=lt)

    def validate(self, value: ComparableType) -> ComparableType:
        if not isinstance(value, (Number, datetime, str)):
            raise ValueError(f"Expected comparable type, got {type(value).__name__}")

        if self.options['ge'] is not None and value < self.options['ge']:
            raise ValueError(f"Value {value} < ge {self.options['ge']}")
        if self.options['le'] is not None and value > self.options['le']:
            raise ValueError(f"Value {value} > le {self.options['le']}")
        if self.options['gt'] is not None and value <= self.options['gt']:
            raise ValueError(f"Value {value} <= gt {self.options['gt']}")
        if self.options['lt'] is not None and value >= self.options['lt']:
            raise ValueError(f"Value {value} >= lt {self.options['lt']}")
        return value


class RegexValidator(ValidatorBase):
    name = "regex"

    def __init__(self, pattern: str|re.Pattern):
        super().__init__(pattern=pattern)
        if isinstance(pattern, str):
            self.regex = re.compile(pattern)
        else:
            self.regex = pattern

    def validate(self, value):
        if not isinstance(value, str):
            raise ValueError(f"Expected string, got {type(value)}")
        if not self.regex.match(value):
            raise ValueError(f"Value '{value}' doesn't match pattern '{self.options['pattern']}'")
        return value


class ChoiceValidator(ValidatorBase):
    name = "choice"

    def __init__(self, choices: Collection):
        super().__init__(choices=choices)
        if not isinstance(choices, Collection):
            raise ValueError(f"Expected collection, got {type(choices)}")

    def validate(self, value):
        if value not in self.options['choices']:
            raise ValueError(f"Value {value} is not in allowed choices: {self.options['choices']}")
        return value
