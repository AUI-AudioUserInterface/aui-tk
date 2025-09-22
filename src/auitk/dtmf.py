from __future__ import annotations
from typing import Optional

class DigitBuffer:
    """Einfache DTMF-Pushback-Queue (falls das Plugin Vorwahlziffern 'zurücklegen' will)."""
    def __init__(self) -> None:
        self._buf: list[str] = []

    def push(self, d: str) -> None:
        if len(d) == 1:
            self._buf.append(d)

    def pop(self) -> Optional[str]:
        return self._buf.pop(0) if self._buf else None
