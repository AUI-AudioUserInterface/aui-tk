from __future__ import annotations
from typing import Iterable, Optional, Tuple, Dict
from .util import Ctx

async def say_wait(ctx: Ctx, text: str) -> None:
    await ctx.say(text, wait=True)

async def confirm(ctx: Ctx, question: str, yes="1", no="2", timeout: float = 10.0) -> Optional[bool]:
    await ctx.say(f"{question} Drücke {yes} für Ja, {no} für Nein.", wait=False)
    d = await ctx.get_digit(timeout)
    if d == yes: return True
    if d == no:  return False
    return None

async def menu(ctx: Ctx, title: str, items: Iterable[Tuple[str, str]], timeout: float = 10.0) -> Optional[str]:
    """
    Einfaches DTMF-Menü.
    items: Liste aus (taste, text).
    Rückgabe: gedrückte Taste oder None.
    """
    parts = [title] + [f"Drücke {k} für {txt}." for (k, txt) in items]
    await ctx.say(" ".join(parts), wait=False)
    digit = await ctx.get_digit(timeout)
    if not digit: return None
    keys = {k for (k, _) in items}
    return digit if digit in keys else None
