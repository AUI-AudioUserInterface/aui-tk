from __future__ import annotations

# Global double-key detection window (seconds) for "**" / "##"
_DOUBLE_KEY_WINDOW: float = 0.50

def set_double_key_window(seconds: float) -> None:
    """Set the global time window for detecting '**' / '##'."""
    global _DOUBLE_KEY_WINDOW
    if seconds < 0.0:
        raise ValueError("double_key_window must be >= 0")
    _DOUBLE_KEY_WINDOW = seconds

def get_double_key_window() -> float:
    """Get the global time window for detecting '**' / '##'."""
    return _DOUBLE_KEY_WINDOW
