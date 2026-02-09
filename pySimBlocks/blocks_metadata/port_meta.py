
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class PortMeta:
    name: str
    display_as: str
    shape: list[Any]
    description: str = ""