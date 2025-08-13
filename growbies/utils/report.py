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