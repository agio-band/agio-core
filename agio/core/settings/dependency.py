from dataclasses import dataclass, field, asdict
from typing import Any


@dataclass
class DependencyConfig:
    type: str|None
    value: Any
    options: dict = field(default_factory=dict)
    enabled: bool = True

    def as_dict(self) -> dict:
        return asdict(self)

    def __bool__(self) -> bool:
        return bool(self.type)


