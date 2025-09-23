from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

from auitk.core.types import Ctx, AuiEvent, AuiEventConfig, InputKind
from .label import Label


@dataclass
class InputLabel:
    """
    Spricht zuerst den Prompt-Text (Label), optional danach einen Hilfetext,
    und liest anschließend Zifferneingaben über DTMF.

    Navigation:
      - '**' -> Abbrechen (None)
      - '##' -> Eingabe abschließen (unter Beachtung enforce_exact_length)
      - '*'  -> alles löschen
      - '#'  -> letzte Ziffer löschen
      - '0'..'9' -> anfügen

    Parameter:
      text: Prompt-Text (zuerst gesprochen)
      max_len:
        >0 -> maximale Länge
         0 -> unbegrenzt (abschließen mit '##' oder durch submit_on_inactivity)
      enforce_exact_length:
        True  -> genau max_len erforderlich; '##' vorher wird ignoriert (mit optionalem Hinweis)
        False -> '##' kann früher abschließen
      auto_submit_on_full:
        True  -> bei max_len>0: sofortige Rückgabe, sobald die Länge erreicht ist
      submit_on_inactivity:
        Nur bei max_len==0. Wenn >0: automatische Rückgabe nach X Sekunden ohne Eingabe
      show_help:
        Wenn True, wird ein kurzer Hilfetext NACH dem Prompt gesprochen (blockierend)
      wait:
        Ob beim Prompt gewartet wird (empfohlen: True, damit Lesen danach startet)
      timeout:
        Per-Read Timeout in Sekunden (gilt NICHT für submit_on_inactivity)
      cfg:
        AuiEventConfig-Schalter (Back/Next/Cancel/Submit aktiv/deaktiviert)
      speak_on_*:
        Kurze Audio-Feedbacks bei Aktionen/Fehlern.
    """
    text: str = "Eingabe bereit."
    max_len: int = 4
    enforce_exact_length: bool = False
    auto_submit_on_full: bool = False
    submit_on_inactivity: Optional[float] = None  # nur bei max_len == 0
    show_help: bool = False
    wait: bool = True
    timeout: float = 10.0
    cfg: Optional[AuiEventConfig] = None

    speak_on_clear: bool = True
    speak_on_backspace: bool = True
    speak_on_too_short_submit: bool = True
    speak_on_max_reached: bool = True
    speak_on_cancel: bool = True

    async def render(self, ctx: Ctx) -> Optional[str]:
        # Lazy-Import hier, um Import-Zyklen sicher zu vermeiden
        from auitk.core.input import read_input_event

        unlimited = self.max_len == 0

        # 1) Prompt (blockierend, damit Lesen erst danach startet)
        await Label(self.text, wait=self.wait).render(ctx)

        # 2) Optional: Hilfe (ebenfalls blockierend)
        if self.show_help:
            if unlimited:
                help_more = ""
                if self.submit_on_inactivity and self.submit_on_inactivity > 0:
                    help_more = f" Automatischer Abschluss nach {int(self.submit_on_inactivity)} Sekunden Inaktivität."
                help_text = (
                    "Bitte gib beliebig viele Ziffern ein und bestätige mit Doppel-Raute."
                    f"{help_more} Doppel-Stern bricht ab. Stern löscht alles, Raute löscht die letzte Ziffer."
                )
            else:
                exact = "genau" if self.enforce_exact_length else "bis zu"
                auto = (
                    "Automatischer Abschluss bei voller Länge."
                    if self.auto_submit_on_full else
                    "Abschluss mit Doppel-Raute."
                )
                help_text = (
                    f"Bitte gib {exact} {self.max_len} Ziffern ein. "
                    f"{auto} Doppel-Stern bricht ab. Stern löscht alles, Raute löscht die letzte Ziffer."
                )
            await Label(help_text, wait=True).render(ctx)

        # 3) Eingabe lesen
        cfg = self.cfg or AuiEventConfig(
            enable_back=True,
            enable_next=True,
            enable_cancel=True,
            enable_submit=True,
        )

        digits: list[str] = []

        while True:
            # Timeout-Strategie:
            # - Unbegrenzt & submit_on_inactivity > 0: pro Read genau dieses Timeout
            # - Sonst: self.timeout
            per_read_timeout: Optional[float]
            if unlimited and self.submit_on_inactivity and self.submit_on_inactivity > 0:
                per_read_timeout = self.submit_on_inactivity
            else:
                per_read_timeout = self.timeout

            ev = await read_input_event(ctx, cfg, timeout=per_read_timeout)

            if ev is None:
                # Timeout:
                # - unbegrenzt + submit_on_inactivity -> aktuellen Stand zurück
                # - ansonsten -> Abbruch
                if unlimited and self.submit_on_inactivity and self.submit_on_inactivity > 0:
                    return "".join(digits) if digits else ""
                return None

            if ev.kind is InputKind.NAV:
                # Abbrechen
                if ev.value is AuiEvent.CANCEL:
                    if self.speak_on_cancel:
                        await ctx.say("Abbruch.", wait=False)
                    return None

                # Abschließen
                if ev.value is AuiEvent.SUBMIT:
                    if not unlimited and self.enforce_exact_length:
                        if len(digits) < self.max_len:
                            if self.speak_on_too_short_submit:
                                remain = self.max_len - len(digits)
                                await ctx.say(
                                    f"Eingabe unvollständig. Es fehlen noch {remain} Zeichen.",
                                    wait=False,
                                )
                            continue
                        return "".join(digits)
                    else:
                        return "".join(digits) if digits else ""

                # Alles löschen
                if ev.value is AuiEvent.BACK:
                    if digits:
                        digits.clear()
                        if self.speak_on_clear:
                            await ctx.say("Eingabe gelöscht.", wait=False)
                    else:
                        if self.speak_on_clear:
                            await ctx.say("Keine Eingabe vorhanden.", wait=False)
                    continue

                # Letzte Ziffer löschen
                if ev.value is AuiEvent.NEXT:
                    if digits:
                        removed = digits.pop()
                        if self.speak_on_backspace:
                            await ctx.say(f"Letzte Ziffer gelöscht: {removed}.", wait=False)
                    else:
                        if self.speak_on_backspace:
                            await ctx.say("Keine Ziffer vorhanden.", wait=False)
                    continue

                # Unbekanntes NAV-Event -> ignorieren
                continue

            # RAW: nur Ziffern
            key = ev.value  # type: ignore[assignment]
            if isinstance(key, str) and key.isdigit():
                if unlimited or len(digits) < self.max_len:
                    digits.append(key)
                    if (not unlimited) and self.auto_submit_on_full and len(digits) == self.max_len:
                        return "".join(digits)
                else:
                    if self.speak_on_max_reached:
                        await ctx.say("Maximale Länge erreicht.", wait=False)
                continue

            # Sonst ignorieren
            continue
