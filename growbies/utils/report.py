from prettytable import PrettyTable
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

def format_float_list(title, headers: list[str], data: list[float]):
    table = PrettyTable(headers)

    table.title = title
    table.float_format = f'.{PRECISION}'
    table.align = 'l'

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
