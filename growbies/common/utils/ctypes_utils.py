from typing import Sequence

def cstring_to_str(char_array: Sequence[int | bytes]) -> str:
    return bytes(char_array).split(b"\0", 1)[0].decode("ascii", errors="ignore")

def set_ctypes_2d_array(array, values: list[list[float]]):
    for row_idx, row in enumerate(values):
        for column_idx, value in enumerate(row):
            array[row_idx][column_idx] = value

def get_ctypes_2d_array(array):
    return [list(array[idx]) for idx in range(len(array))]