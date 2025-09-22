from __future__ import annotations
from typing import Optional
from .util import Ctx

async def say(ctx: Ctx, text: str, wait: bool = True) -> None:
    await ctx.say(text, wait=wait)

async def say_and_get_digit(ctx: Ctx, text: str, timeout: float = 10.0) -> Optional[str]:
    await ctx.say(text, wait=False)
    return await ctx.get_digit(timeout)

async def say_and_get_number(ctx: Ctx, text: str, max_len: int = 6, timeout: float = 10.0) -> Optional[str]:
    """Fragt eine Zahl per DTMF ab (0-9, optional # als Abschluss)."""
    await ctx.say(text, wait=False)
    digits: list[str] = []
    while len(digits) < max_len:
        d = await ctx.get_digit(timeout)
        if d is None:
            break
        if d == "#":
            break
        if d.isdigit():
            digits.append(d)
    return "".join(digits) if digits else None
