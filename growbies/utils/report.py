PRECISION = 8

def format_float_table(data, headers):
    """
    Prints a 2D list of floats as a formatted table with column headers.

    Args:
        data (list of lists): The 2D list of floats to print.
        headers (list of str): A list of strings representing the column headers.
    """
    table = list()

    # Calculate maximum width for each column
    column_widths = [len(header) for header in headers]
    for row in data:
        for i, item in enumerate(row):
            # Format floats to 2 decimal places
            column_widths[i] = max(column_widths[i], len(f'{item:.{PRECISION}f}'))

    # Print headers
    header_format = ' '.join([f"{{:<{width}}}" for width in column_widths])
    table.append(header_format.format(*headers))
    table.append("-" * (sum(column_widths) + len(column_widths) - 1)) # Separator line

    # Print data rows
    for row in data:
        row_strings = [f"{item:<{column_widths[i]}.{PRECISION}f}" for i, item in enumerate(row)]
        table.append(" ".join(row_strings))

    return '\n'.join(table)
