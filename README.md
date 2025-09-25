# aui-tk (LGPL)

Skeleton für eine einfache Tk-Anbindung in AUI.

- Künftige Idee: Buttons oder Hotkeys erzeugen DTMF-Events (`push_digit()`).
- Der Core setzt nach dem Laden: `adapter.push_digit = ctx.digit_buffer.push_digit`.

## Entry Point
- Gruppe: `aui.adapters`
- Name: `tk`
- Klasse: `TkAdapter`
