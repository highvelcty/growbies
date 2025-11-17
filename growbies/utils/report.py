from uuid import UUID
from prettytable import PrettyTable
from typing import Optional
import textwrap

from growbies.constants import TABLE_COLUMN_WIDTH

PRECISION = 6

def format_float_table(title, headers: list[str], data: list[list[float]]) -> str:
    """
    Prints a 2D list of floats as a formatted table with title and column headers.
    """

    table = PrettyTable(headers)

    table.title = title
    table.float_format = f'.{PRECISION}'
    table.align = 'l'

    for row_idx, row in enumerate(data):
        table.add_row([row_idx] + row)


    return str(table)

def format_float_list(title, headers: list[str], datas: list[list[float]]):
    table = PrettyTable(headers)

    table.title = title
    table.float_format = f'.{PRECISION}'
    table.align = 'l'

    for data in datas:
        table.add_row(data)

    return str(table)

def format_8bit_binary(num: int) -> str:
    bin_str = f'{num:08b}'
    return ' '.join(bin_str[i:i+4] for i in range(0, 8, 4))


def format_dropped_bytes(buf: bytearray | bytes | memoryview ) -> str:
    max_display = 16
    buf = bytes(buf)

    length = len(buf)

    if length == 0:
        return 'empty frame'

    if length <= max_display:
        # Show all bytes
        return str(buf)
    else:
        # Show first 8 and last 8 bytes with ellipsis
        first_part = buf[:max_display // 2]
        last_part = buf[-max_display // 2:]
        # Format like a normal bytes literal
        repr_bytes = repr(first_part)[:-1] + '...' + repr(last_part)[2:]
        return f'{repr_bytes} of length {length}'

def list_str_wrap(the_list, wrap=4, indent=1) -> str:
    """Return a string of values with line breaks every `wrap` elements,
    indented `indent` spaces after the first line.

    Floats are shown with 2 decimals, ints as ints, and strings as-is.
    """
    if not the_list:
        return "[]"

    def fmt(x):
        if isinstance(x, float):
            return f"{x:.2f}"
        else:
            return str(x)

    formatted = [fmt(x) for x in the_list]

    lines = []
    for i in range(0, len(formatted), wrap):
        lines.append(", ".join(formatted[i:i + wrap]))

    result = "[" + lines[0]
    for line in lines[1:]:
        result += ",\n" + " " * indent + line
    result += "]"
    return result

def short_uuid(uuid: str | UUID):
    return str(uuid)[:7]

def wrap_for_column(col_str: Optional[str]) -> str:
    if col_str is None:
        return ''
    wrapped_lines = []
    for line in col_str.splitlines():
        wrapped_lines.extend(textwrap.wrap(line, width=TABLE_COLUMN_WIDTH) or [''])
    return '\n'.join(wrapped_lines)

def decode_escapes(a_str: Optional[str]) -> Optional[str]:
    if a_str is None:
        return a_str
    return a_str.replace('\\n', '\n').replace('\\t', '\t').replace('\\r', '\r')
