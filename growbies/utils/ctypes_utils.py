from typing import Sequence

def cstring_to_str(char_array: Sequence[int | bytes]) -> str:
    return bytes(char_array).split(b"\0", 1)[0].decode("ascii", errors="ignore")
