# src/auitk/widgets/menu.py
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional

from auitk.core.types import Ctx, AuiEvent, AuiEventConfig, InputKind
from .label import Label


@dataclass
class Menu:
    """
    Paged DTMF menu (page size fixed to 10).
    Keys:
      1..9 -> item 1..9 on current page
      0    -> item 10 on current page
      *    -> previous page (with boundary notice, no wrap)
      #    -> next page (with boundary notice, no wrap)
      **   -> abort menu (returns None)
      ##   -> select default (if set) when no pending selection

    Parameters
    ----------
    title : str
        Menu title (spoken at start; optionally on every page change).
    items : List[str]
        Spoken labels for items; return value is the 0-based index into this list.
    confirm : bool
        If True, selecting a digit enters a confirmation step:
          "**" -> back to page (not abort), "##" -> accept selection.
        If False, selection returns immediately.
    default_index : Optional[int]
        If set and valid, pressing "##" in the menu (no pending selection) selects this entry.
    announce_title_on_every_page : bool
        If True, speak the title on every page change as well.
    timeout : float
        Per-key timeout (seconds). Timeout -> returns None.
    wait_prompts : bool
        If True, prompts are blocking (so the timeout starts after speaking).
    cfg : Optional[AuiEventConfig]
        Event toggles; double-key window is global (auitk.core.config).
    """
    title: str
    items: List[str]
    confirm: bool = False
    default_index: Optional[int] = None
    announce_title_on_every_page: bool = False
    timeout: float = 10.0
    wait_prompts: bool = True
    cfg: Optional[AuiEventConfig] = None

    async def render(self, ctx: Ctx) -> Optional[int]:
        # Lazy import to avoid any potential import cycles
        from auitk.core.input import read_input_event

        n = len(self.items)
        if n == 0:
            await Label(self.title, wait=self.wait_prompts).render(ctx)
            await Label("Es sind keine Einträge verfügbar.", wait=self.wait_prompts).render(ctx)
            return None

        page_size = 10
        pages = (n + page_size - 1) // page_size
        page = 0  # 0-based
        cfg = self.cfg or AuiEventConfig(
            enable_back=True,    # "*"
            enable_next=True,    # "#"
            enable_cancel=True,  # "**"
            enable_submit=True,  # "##"
        )

        pending_index: Optional[int] = None  # global item index while confirming

        # Helpers
        async def say_title_and_page(on_change: bool) -> None:
            if on_change:
                if self.announce_title_on_every_page:
                    await Label(self.title, wait=self.wait_prompts).render(ctx)
            else:
                # initial call -> always say title
                await Label(self.title, wait=self.wait_prompts).render(ctx)
            await Label(f"Sie befinden sich auf Seite {page+1} von {pages}.",
                        wait=self.wait_prompts).render(ctx)

        def page_range() -> range:
            start = page * page_size
            end = min(start + page_size, n)
            return range(start, end)

        async def say_navigation_hints() -> None:
            has_prev = page > 0
            has_next = page < pages - 1
            if has_prev and has_next:
                await Label("Mit Stern zur vorherigen, mit Raute zur nächsten Seite.",
                            wait=self.wait_prompts).render(ctx)
            elif has_prev:
                await Label("Mit Stern zur vorherigen Seite.",
                            wait=self.wait_prompts).render(ctx)
            elif has_next:
                await Label("Mit Raute zur nächsten Seite.",
                            wait=self.wait_prompts).render(ctx)

        async def say_page_items() -> None:
            rng = page_range()
            if not rng:
                await Label("Keine Einträge auf dieser Seite.", wait=self.wait_prompts).render(ctx)
                await say_navigation_hints()
                return
            parts = []
            parts.append("Drücken Sie folgende Taste: ")
            for i, gi in enumerate(rng, start=1):  # i: 1..k (k<=10), gi: global index
                key_spoken = "0" if i == 10 else str(i)   # 0 steht für den 10. Eintrag
                parts.append(f"{key_spoken} für {self.items[gi]},")

            # Vorletztes Element: letztes Komma durch " und"
            if len(parts) >= 2:
                left, right = parts[-2].rsplit(",", 1)
                parts[-2] = left + " und" + right

            # Letztes Element: letztes Komma durch "."
            left, right = parts[-1].rsplit(",", 1)
            parts[-1] = left + "." + right

            await Label(" ".join(parts), wait=self.wait_prompts).render(ctx)
            # Wenn weniger als 10 Einträge auf der Seite existieren
            if len(rng) < page_size:
                await Label("Keine weiteren Einträge auf dieser Seite.", wait=self.wait_prompts).render(ctx)
            # Navigationshinweise (falls anwendbar)
            await say_navigation_hints()

        async def announce_selection(idx: int) -> None:
            await Label(f"Ausgewählt: {self.items[idx]}.", wait=self.wait_prompts).render(ctx)
            if self.confirm:
                await Label("Doppel-Stern: zurück. Doppel-Raute: übernehmen.",
                            wait=self.wait_prompts).render(ctx)

        # Initial announcement
        await say_title_and_page(on_change=False)
        await say_page_items()
        if self.default_index is not None and 0 <= self.default_index < n:
            await Label(f"Doppel-Raute wählt den Standard: {self.items[self.default_index]}.",
                        wait=self.wait_prompts).render(ctx)

        # Main loop
        while True:
            ev = await read_input_event(ctx, cfg, timeout=self.timeout)
            if ev is None:
                return None  # Timeout

            if ev.kind is InputKind.NAV:
                if ev.value is AuiEvent.CANCEL:
                    # "**" : abort (außer wir sind in der Bestätigung → zurück zur Seite)
                    if pending_index is None:
                        return None
                    pending_index = None
                    await say_title_and_page(on_change=True)
                    await say_page_items()
                    continue

                if ev.value is AuiEvent.SUBMIT:
                    # "##" : confirm if pending; else default if set
                    if pending_index is not None:
                        return pending_index
                    if self.default_index is not None and 0 <= self.default_index < n:
                        await Label(f"Standardauswahl übernommen: {self.items[self.default_index]}.",
                                    wait=self.wait_prompts).render(ctx)
                        return self.default_index
                    else:
                        await Label("Kein Standard definiert.", wait=self.wait_prompts).render(ctx)
                        await say_title_and_page(on_change=True)
                        await say_page_items()
                        continue

                if ev.value is AuiEvent.BACK:
                    # "*" : previous page (no wrap)
                    if page == 0:
                        await Label("Keine vorherige Seite.", wait=self.wait_prompts).render(ctx)
                        await say_title_and_page(on_change=True)
                        await say_page_items()
                    else:
                        page -= 1
                        pending_index = None
                        await say_title_and_page(on_change=True)
                        await say_page_items()
                    continue

                if ev.value is AuiEvent.NEXT:
                    # "#" : next page (no wrap)
                    if page >= pages - 1:
                        await Label("Keine weitere Seite.", wait=self.wait_prompts).render(ctx)
                        await say_title_and_page(on_change=True)
                        await say_page_items()
                    else:
                        page += 1
                        pending_index = None
                        await say_title_and_page(on_change=True)
                        await say_page_items()
                    continue

                # Unknown NAV -> ignore
                continue

            # RAW input: expect single digit
            key = ev.value  # type: ignore[assignment]
            if isinstance(key, str) and key.isdigit() and len(key) == 1:
                d = int(key)
                slot = 9 if d == 0 else d - 1  # 0 -> slot 9 (10. Eintrag)
                start = page * page_size
                rng = list(page_range())
                if slot < len(rng):
                    gi = rng[slot]
                    if self.confirm:
                        pending_index = gi
                        await announce_selection(gi)
                    else:
                        await announce_selection(gi)
                        return gi
                else:
                    await Label("Ungültige Auswahl.", wait=self.wait_prompts).render(ctx)
                    await say_title_and_page(on_change=True)
                    await say_page_items()
                continue

            # Other RAW ignored
            continue
