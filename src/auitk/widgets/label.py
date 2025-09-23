from __future__ import annotations
from dataclasses import dataclass
from typing import Awaitable, Callable, Optional, Protocol, Union

from auitk.core.types import Ctx


class Widget(Protocol):
    """Base protocol for AUI widgets."""
    async def render(self, ctx: Ctx) -> None: ...


TextSource = Union[str, Callable[[], str], Callable[[], Awaitable[str]]]
TextFormatter = Callable[[str], str]


async def _resolve_text(src: TextSource) -> str:
    if isinstance(src, str):
        return src
    val = src()
    if isinstance(val, str):
        return val
    # assume awaitable
    return await val


@dataclass
class Label(Widget):
    """
    A simple, non-interactive label that speaks a given text.
    - text: static string or callable/async callable returning a string
    - wait: if True, block until TTS finished
    - formatter: optional text post-processor (e.g., symbol mapping)
    """
    text: TextSource
    wait: bool = True
    formatter: Optional[TextFormatter] = None

    async def render(self, ctx: Ctx) -> None:
        lText = await _resolve_text(self.text)
        if self.formatter:
            lText = self.formatter(lText)
        await ctx.say(lText, wait=self.wait)
