
class TkAdapter:
    def __init__(self) -> None:
        self.push_digit = lambda ch: None  # core setzt diese Funktion
    def speak(self, text: str) -> None: print(f"[TK] speak: {text}")
    def stop_speak(self) -> None: print("[TK] stop_speak")
    def play(self, uri: str) -> None: print(f"[TK] play: {uri}")
    def stop_play(self) -> None: print("[TK] stop_play")
    def ring(self) -> None: print("[TK] ring")
    def hangup(self) -> None: print("[TK] hangup")
