from __future__ import annotations
from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional, Protocol, Union

class Ctx(Protocol):
    async def say(self, text: str, wait: bool = False) -> None: ...
    async def get_digit(self, timeout: Optional[float] = None) -> Optional[str]: ...

class AuiEvent(Enum):
    BACK   = auto()   # "*"  (left/back)
    NEXT   = auto()   # "#"  (right/forward)
    CANCEL = auto()   # "**" (abort)
    SUBMIT = auto()   # "##" (enter)

@dataclass(frozen=True)
class AuiEventConfig:
    enable_back:   bool = True
    enable_next:   bool = True
    enable_cancel: bool = True
    enable_submit: bool = True
    inter_event_window: float = 0.35  # seconds for "**"/"##"

class InputKind(Enum):
    NAV = auto()
    RAW = auto()

@dataclass(frozen=True)
class InputEvent:
    kind: InputKind
    value: Union[AuiEvent, str]      # NAV: AuiEvent, RAW: "0"-"9","*","#","**","##"
    ts: float                        # event timestamp (monotonic)
