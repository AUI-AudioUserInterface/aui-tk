from __future__ import annotations
import asyncio
from typing import AsyncIterator, Optional
from .types import Ctx, AuiEventConfig, InputEvent
from .input import read_input_event

class InputLoop:
    """
    Einfache Eingabe-EventLoop:
      - run(): produziert kontinuierlich InputEvent-Objekte (async generator)
      - stop(): sauberes Stoppen per Flag/Cancel
    """
    def __init__(self, ctx: Ctx, cfg: Optional[AuiEventConfig] = None) -> None:
        self._ctx = ctx
        self._cfg = cfg or AuiEventConfig()
        self._stopped = asyncio.Event()

    def stop(self) -> None:
        self._stopped.set()

    async def run(self, per_key_timeout: float = 30.0) -> AsyncIterator[InputEvent]:
        """
        Erzeugt Events, sobald Tasten kommen. Timeout pro Tastenschritt
        verhindert blockierende Hänger; None wird übersprungen.
        """
        while not self._stopped.is_set():
            ev = await read_input_event(self._ctx, self._cfg, timeout=per_key_timeout)
            if ev is None:
                # Timeout: einfach weiter warten (oder yield eines speziellen Timeout-Events, falls gewünscht)
                continue
            yield ev
