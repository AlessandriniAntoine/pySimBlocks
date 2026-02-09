
from dataclasses import dataclass, field
from typing import Any, List, Optional


@dataclass(frozen=True)
class ParameterMeta:
    name: str
    type: str
    required: bool = False
    autofill: bool = False
    default: Optional[Any] = None
    enum: List[Any] = field(default_factory=list)
    description: str = ""
