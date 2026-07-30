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
FUZZY_MAX_EXTENSION = 2

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



def dissect_string(raw_search_term: str) -> dict[str, list[str]]:
    """Sanitize the users search term.

    Returns a dict of original search term to
    list of lowered and stripped and split on whitespaces.
    """
    return {raw_search_term: raw_search_term.lower().strip().split()}


def get_similar(
    db: list[str],
    search_term: str,
    fuzzy_threshold: int = FUZZY_DIST,
    max_threshold_extension: int = FUZZY_MAX_EXTENSION,
    *,
    always_fuzzy: bool = False,
    print_table: bool = False,
) -> list:
    """Return similar words.

    Looks for direct matches of any part of the search term in any
    part of the db items. Does not consider capitalization.
    If null found it uses a basic Fussy Search bound by fuzzy_threshold.
    The fuzzy search only considers parts of the db items in the length
    of the length of the original search term parts to better match
    small typos.
    Can take multi part search terms and or db items. Both get lowered
    for comparison and stripped off and by whitespaces.
    Does not sanitize by any other means.
    Optionally prints (every!) table.

    Args:
        db (list[str]): The items to be searched.
        search_term (str): The search term to be looked for.
        fuzzy_threshold (int): The max distance to count as match.

    Returns:
        list[str]: All found matches, sorted by distance.

    """
    search_results: list[tuple] = []
    search_term_split = dissect_string(search_term)
    unique_direct_finds = {}  # dict, not set to prev. same finds by diff. dist
    unique_fuzzy_finds = {}
    for item in db:
        item_split = dissect_string(item)
        item_lowered = item.lower()
        # direct matches?
        # search for direct matches of any part of the search term(s)
        # directly being part of one of the db items.
        for st in search_term_split[search_term]:
            if st in item_lowered:
                # we dont strictly need dist here. used to sort results.
                direct_dist = _calc_distance(
                    st,
                    item_lowered,
                )
                # if found prev., keep only smaller dist
                prev_find_dist = unique_direct_finds.get(item)
                if not prev_find_dist or prev_find_dist > direct_dist:
                    unique_direct_finds[item] = direct_dist

        # if no direct matches found or param set
        # look for off by fuzzy_threshold mistakes
        # exclude already found items
        if (
            not unique_direct_finds or always_fuzzy
        ) and item not in unique_direct_finds:
            for search_term_part in search_term_split[search_term]:
                for item_part in item_split[item]:
                    short_item_part = item_part[: len(search_term_part) + 1]
                    fuzzy_dist = _calc_distance(
                        search_term_part,
                        short_item_part,
                        print_table=print_table,
                    )

                    if fuzzy_dist <= fuzzy_threshold + max_threshold_extension:
                        # if found prev., keep only smaller dist
                        prev_fuzzy_find_dist = unique_fuzzy_finds.get(item)
                        if (
                            not prev_fuzzy_find_dist
                            or prev_fuzzy_find_dist > fuzzy_dist
                        ):
                            unique_fuzzy_finds[item] = fuzzy_dist

    fuzzy_finds_extended_list_sorted = sorted(
        unique_fuzzy_finds.items(),
        key=lambda dist: dist[1],
    )

    # refine fuzzy results:
    # findings include all for dist + max_threshold_extension.
    # this will find "Meister Eder" for "bla", bc Eder-bla dist = 4. So
    # reduce results to findings with minimal distance by increasing
    # dist by one up to fuzzy_threshold + max_threshold_extension.
    # worst case: if eder-bla is the only match, this will be returned.
    # tbd if useful.
    closest_fuzzy_find = None
    exp_step = 0
    while not closest_fuzzy_find and exp_step <= max_threshold_extension:
        # walk all finds backwards until some find with minimal dist.
        # expects fuzzy finds sorted.
        min_dist = fuzzy_threshold - max_threshold_extension + exp_step
        closest_fuzzy_find = [
            (find, dist)
            for find, dist in fuzzy_finds_extended_list_sorted
            if dist == min_dist
        ]
        exp_step += 1

    unique_direct_finds = sorted(
        unique_direct_finds.items(),
        key=lambda dist: dist[1],
    )

    search_results.extend(unique_direct_finds)
    if closest_fuzzy_find:
        # important to append and end bc dist of fuzzy finding are only
        # per split search terms vs split item.
        search_results.extend(closest_fuzzy_find)
    return search_results


if __name__ == "__main__":
    testdb = [
        "the bl",
        "the bla2",
        "hurtz bla",
        "blap",
        "the longest blubb",
        "Meister Eder",
    ]
    testsearch = input("seach term: ")
    print(f"searchterm: {testsearch} testdata: {testdb}")
    testthreshold = 5
    print(f"results: {get_similar(testdb, testsearch, always_fuzzy=True)}")
