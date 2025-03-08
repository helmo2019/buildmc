"""Logging functionality"""

from sys import stderr, stdout


log_info = 0
log_warn = 1
log_error = 2

def _ansi(seq: str) -> str:
    return f"\033[{seq}m"

_f = {
    "r": _ansi("0"),    # Reset
    "b": _ansi("1"),    # Bold
    "n": _ansi("22"),   # Normal intensity
    "yellow": _ansi("38;2;219;185;42"), # Custom yellow
    "red": _ansi("38;2;221;42;84")      # Custom red
}


def log(msg: str, level: int = 0):
    """Print styled log message to appropriate output stream"""

    print(
        (f"{_f['b']}ℹ{_f['n']}" if level == log_info else
        f"⚠{_f['yellow']}" if level == log_warn else
        f"{_f['red']}{_f['b']}⮾{_f['n']}")
        +f" {msg}{_f['r']}"
    , file=stderr if level > log_info else stdout)