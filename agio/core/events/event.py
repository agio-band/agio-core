import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict

from agio.core.exceptions import EventNameError, EventCreationError

NAME_PATTERN = re.compile(r"^[A-Za-z][\w-]+\.[\w-]+\.[\w-]+$")


@dataclass(slots=True, frozen=True)
class AEvent:
    name: str
    sender: str|None
    payload: dict|None = None
    emit_time: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        if not NAME_PATTERN.match(self.name):
            raise EventNameError(f"Event name '{self.name}' is invalid. Valid pattern: package.process.action")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "sender": self.sender,
            "creation_date": self.emit_time.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AEvent':
        try:
            name = str(data["name"])
            sender = str(data["sender"])
            emit_time_str = data.get("emit_time")
            emit_time = datetime.fromisoformat(emit_time_str) if emit_time_str else datetime.now()
        except (KeyError, ValueError, TypeError) as e:
            raise EventCreationError(f"Invalid data for AEvent: {e}")

        return cls(name=name, sender=sender, emit_time=emit_time)
