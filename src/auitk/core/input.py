from __future__ import annotations
import time
from typing import Optional

from .types import Ctx, AuiEvent, AuiEventConfig, InputEvent, InputKind
from .config import get_double_key_window  # globales Zeitfenster für "**"/"##"


async def read_input_event(
    ctx: Ctx,
    cfg: AuiEventConfig,
    timeout: Optional[float] = None,
) -> Optional[InputEvent]:
    """
    Liest eine Taste und mappt sie auf NAV-Event (falls aktiviert) oder RAW-String.
    - "*"  -> BACK (wenn enable_back)
    - "#"  -> NEXT (wenn enable_next)
    - "**" -> CANCEL (wenn enable_cancel), sonst "**" roh
    - "##" -> SUBMIT (wenn enable_submit), sonst "##" roh
    - Ziffern "0".."9" -> RAW
    Gibt None bei Timeout.
    Hinweis: Kein Pushback – ein zweites, verschiedenes Zeichen im Doppel-Fenster wird verworfen.
    """
    first = await ctx.get_digit(timeout)
    if first is None:
        return None

    now = time.monotonic()

    # Nicht Stern/Raute: direkt als RAW zurück
    if first not in ("*", "#"):
        return InputEvent(InputKind.RAW, first, now)

    # Doppel-Erkennung mit GLOBALER Zeit
    window = get_double_key_window()
    second = await ctx.get_digit(window)

    if second == first:
        now = time.monotonic()
        if first == "*":
            return (
                InputEvent(InputKind.NAV, AuiEvent.CANCEL, now)
                if cfg.enable_cancel
                else InputEvent(InputKind.RAW, "**", now)
            )
        else:  # "#"
            return (
                InputEvent(InputKind.NAV, AuiEvent.SUBMIT, now)
                if cfg.enable_submit
                else InputEvent(InputKind.RAW, "##", now)
            )

    # Kein Doppel (oder anderes zweites Zeichen -> wird verworfen)
    now = time.monotonic()
    if first == "*":
        return (
            InputEvent(InputKind.NAV, AuiEvent.BACK, now)
            if cfg.enable_back
            else InputEvent(InputKind.RAW, "*", now)
        )
    else:
        return (
            InputEvent(InputKind.NAV, AuiEvent.NEXT, now)
            if cfg.enable_next
            else InputEvent(InputKind.RAW, "#", now)
        )
