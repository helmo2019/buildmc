"""Some ANSI escape codes for styling"""


def _ansi(seq: str) -> str:
    return f'\033[{seq}m'


bold = _ansi('1')
not_bold = _ansi('22')  # "Normal intensity"
green = _ansi('38;2;98;204;22')
yellow = _ansi('38;2;219;185;42')
red = _ansi('38;2;247;32;82')
gray = _ansi('38;2;150;150;150')
purple = _ansi('38;2;122;41;165')
blue = _ansi('38;2;79;141;234')
light_blue = _ansi('38;2;78;152;216')
italic = _ansi('3')
not_italic = _ansi('23')

reset = _ansi('0')
