import json
import textwrap


def print_json_as_table(data, title=None, wrap_length=500):
    """
    Prints a list of flat dictionaries or a JSON string representing such a list as a formatted table with automatic
    wrapping.

    :param data: A JSON string or list of dictionaries representing the table data. Each dict is a row in the table.
    :type data: str or list
    :param title: An optional title to be printed above the table. Defaults to None.
    :type title: str, optional
    :param wrap_length: The maximum number of characters for each line in a cell before wrapping to the next line.
                        Defaults to 500.
    :type wrap_length: int

    The function prints the formatted table directly to the standard output.

    Example usage:
    json_data = '[{"Name": "Alice", "Age": 30}, {"Name": "Bob", "Age": 25}]'
    print_json_as_table(json_data, "Example Table", wrap_length=10)
    """

    # data = json.loads(json_data)
    # If the input is a string, assume it's a JSON string and parse it
    if isinstance(data, str):
        data = json.loads(data)

    # Ensure data is a list of dictionaries
    if not isinstance(data, list) or not all(isinstance(item, dict) for item in data):
        raise ValueError(
            "Data must be a list of dictionaries or a JSON string representing such a list."
        )

    # Create headers
    headers = data[0].keys()

    # Wrap text for each row and find the maximum width for each column
    col_widths = {h: len(h) for h in headers}
    for row in data:
        for h in headers:
            cell = str(row[h])
            wrapped = (
                textwrap.wrap(cell, width=wrap_length)
                if len(cell) > wrap_length
                else [cell]
            )
            col_widths[h] = max(col_widths[h], max(len(w) for w in wrapped))

    # Add extra space for padding and vertical separators
    total_width = sum(col_widths.values()) + 3 * (len(headers) - 1) + 4

    # Calculate and print the separator line
    sep_line = "-" * total_width
    print(sep_line)

    # Print the title, if provided
    if title:
        print("| " + f"{title.center(total_width - 4)} " + "|")
        print(sep_line)

    # Print the headers
    # print("| " + " | ".join(f"{h.title():{col_widths[h]}}" for h in headers) + " |")
    # print(sep_line)
    print("| " + " | ".join(f"{h.title():^{col_widths[h]}}" for h in headers) + " |")
    print(sep_line)

    # Print each row with wrapped text
    for row in data:
        wrapped_rows = {
            h: textwrap.wrap(str(row[h]), width=col_widths[h]) for h in headers
        }
        max_lines = max(len(wrapped) for wrapped in wrapped_rows.values())
        for line_idx in range(max_lines):
            line = "| "
            for h in headers:
                cell = (
                    wrapped_rows[h][line_idx] if line_idx < len(wrapped_rows[h]) else ""
                )
                line += f"{cell:{col_widths[h]}} | "
            print(line)
        print(sep_line)
