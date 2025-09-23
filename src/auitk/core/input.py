from __future__ import annotations
import time
from typing import Optional
from .types import Ctx, AuiEvent, AuiEventConfig, InputEvent, InputKind

async def read_input_event(
    ctx: Ctx,
    cfg: AuiEventConfig,
    timeout: Optional[float] = None,
) -> Optional[InputEvent]:
    """
    Liest eine Taste und bildet sie auf NAV-Event (falls aktiviert) oder RAW ab.
    Gibt None bei Timeout zurück.
    """
    t0 = time.monotonic()
    first = await ctx.get_digit(timeout)
    if first is None:
        return None

    if first not in ("*", "#"):
        return InputEvent(InputKind.RAW, first, time.monotonic())

    # Doppel-Erkennung mit kleinem Zeitfenster
    second = await ctx.get_digit(cfg.inter_event_window)
    if second == first:
        now = time.monotonic()
        if first == "*":
            if cfg.enable_cancel:
                return InputEvent(InputKind.NAV, AuiEvent.CANCEL, now)
            else:
                return InputEvent(InputKind.RAW, "**", now)
        else:  # "#"
            if cfg.enable_submit:
                return InputEvent(InputKind.NAV, AuiEvent.SUBMIT, now)
            else:
                return InputEvent(InputKind.RAW, "##", now)

    # Kein Doppel – ggf. second zurückpuffern? (bewusst: nein)
    # Begründung: auicore liefert Tastendrücke einzeln; ein „versehentlicher" Read hier
    # würde Semantik verkomplizieren. Wenn nötig, können wir später einen Buffer ergänzen.

    now = time.monotonic()
    if first == "*":
        if cfg.enable_back:
            return InputEvent(InputKind.NAV, AuiEvent.BACK, now)
        else:
            return InputEvent(InputKind.RAW, "*", now)
    else:
        if cfg.enable_next:
            return InputEvent(InputKind.NAV, AuiEvent.NEXT, now)
        else:
            return InputEvent(InputKind.RAW, "#", now)
