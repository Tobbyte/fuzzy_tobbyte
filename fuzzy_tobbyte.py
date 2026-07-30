"""Fuzzy Search implementation using naive Levenshtein algorithm."""

"""
Limitations:
    - doest not optimize search in any meaningful way
"""

"""
 ~ Made with ❤️ and without ai or code completion (except intelliSense) ~
"""

"""
TODO:
  - extend docstring by what fn is used for
"""
__all__ = ["get_similar"]  # public method

FUZZY_DIST = 2

def _print_fuzzy_table(table: list, str1: str, str2: str) -> None:
    """Pretty print the table."""
    header = str1
    column = str2

    first_col_w = len(column)
    cell_w = len(header)

    # header Row
    header_row: list[str] = ["_"]
    for i in range(len(header)):
        header_row.append(header[: i + 1])  # noqa: PERF401

    # body rows
    display_rows: list[list[str | int]] = []
    original_row: list[int | str] = []

    for i, original_row in enumerate(table):
        row_copy = list(original_row)
        row_prefix = "_" if i == 0 else column[:i]
        row_copy.insert(0, row_prefix)
        display_rows.append(row_copy)

    print()

    # Print header Row
    print("▦".rjust(first_col_w), end="")
    # Align to first data column
    print(" " * (first_col_w + 1), end="")

    for cell in header_row:
        print(str(cell).ljust(cell_w + 1), end="")

    print("\n")

    # print data rows
    for row in display_rows:
        # first cell (row labels)
        print(str(row[0]).rjust(first_col_w), end=" ")

        for cell in row[1:]:
            print(str(cell).rjust(cell_w), end=" ")
        print("\n")


def _calc_distance(
    search_term: str,
    compar_term: str,
    *,
    print_table: bool = False,
) -> int:
    """Calculate the distance between inputs."""
    data_matrix = _init_table(search_term, compar_term)

    for row in range(1, len(data_matrix)):
        for column in range(1, len(data_matrix[row])):
            left_cell = data_matrix[row][column - 1] + 1
            top_cell = data_matrix[row - 1][column] + 1
            diag_top_char = search_term[column - 1]
            diag_left_char = compar_term[row - 1]
            diag_is_diff = 0

            if diag_top_char != diag_left_char:
                diag_is_diff = 1
            diag = data_matrix[row - 1][column - 1] + diag_is_diff
            data_matrix[row][column] = min(left_cell, top_cell, diag)

    if print_table:
        print("\n\n\n\n\n\n")
        _print_fuzzy_table(data_matrix, search_term, compar_term)
        print(f"distance: {data_matrix[-1][-1]}")

    return data_matrix[-1][-1]


def _init_table(str1: str, str2: str) -> list:
    """Initialize the table for distance calculation."""
    data_matrix: list = []

    for i in range(len(str2) + 1):
        row = []
        for j in range(len(str1) + 1):  # len word + extra 0
            if i == 0:
                # top row
                row.append(j)
            elif j == 0:
                # left column
                row.append(i)
            else:
                row.append(-1)
        data_matrix.append(row)

    return data_matrix



def sanitize_search_term(raw_search_term: str) -> dict[str, list[str]]:
    """Sanitize the users search term.

    Returns a dict of original search term to
    list of lowered and stripped and split on whitespaces.
    """
    return {raw_search_term: raw_search_term.lower().strip().split()}


def get_similar(
    db: list[str],
    search_term: str,
    threshold: int,
    *,
    print_table: bool = False,
) -> list:
    """Return similar words.

    Uses a basic Fussy Search over list:[str] of items and returns
    similar items and their distance to comparison term[str].
    Takes a threshold for the distance calculation and optionally
    prints (every) table
    """
    similar_results: list[tuple] = []
    st_lowered_san = sanitize_search_term(search_term)
    unique_direct_finds = set()
    for item in db:
        san_item = sanitize_search_term(item)
        item_lowered = item.lower()

        # direct matches?
        # search for direct matches of any part of the search term(s)
        # directly being part of one of the db items (parts).
        for st in st_lowered_san[search_term]:
            if st in item_lowered:
                unique_direct_finds.add(item_lowered)

        # if no direct matches found, look for off by two mistakes
        fuzzy_by_one_finds = set()
        if not unique_direct_finds:
            # für jeden teil vom search term
            # calc distance zu jedem teil vom item
            # wenn dist == FUZZY_DIST its off by one
            # nehme nur die länge vom search term teil zum vergleich
            for search_term_part in st_lowered_san[search_term]:
                for item_part in san_item[item]:
                    short_item_part = item_part[: len(search_term_part) + 1]
                    dist = _calc_distance(
                        search_term_part,
                        short_item_part,
                        print_table=print_table,
                    )
                    if dist == FUZZY_DIST:
                        fuzzy_by_one_finds.add((item, search_term))

    for find in unique_direct_finds:
        print(f"direct: '{find}' found by '{search_term}'")
    for find in fuzzy_by_one_finds:
        print(f"fuzzy: '{find}' found by '{search_term}'")

    return sorted(similar_results, key=lambda dist: dist[1])


if __name__ == "__main__":
    testdb = [
        "the bl",
        "the bla2",
        "hurtz bla",
        "blap",
        "the longest blubb",
        "Meister Eder",
    ]
    testsearch = "Moster"
    print(f"searchterm: {testsearch} testdata: {testdb}")
    testthreshold = 5
    print(get_similar(testdb, testsearch, testthreshold))
