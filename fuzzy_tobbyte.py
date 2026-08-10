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

# TODO:
# - sets even when filled double (item, dist_a), (same_item, dist_b)
#   instead of dicts?
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
    Since fuzzy results have potentially reconstructed distances, the
    returned dist is contrary expectation not necessary bound by
    fuzzy_threshold + max_threshold_extension.
    Optionally prints (every!) table.

    Args:
        db (list[str]): The items to be searched.
        search_term (str): The search term to be looked for.
        fuzzy_threshold (int): The max distance to count as match.

    Returns:
        list[str]: All found matches, sorted by distance.

    """
    search_term_split = dissect_string(search_term)[search_term]
    direct_finds = {}  # dict, not set to prev. same finds by diff. dist
    fuzzy_finds = {}  # dict, not set to prev. same finds by diff. dist
    for item in db:
        item_split = dissect_string(item)[item]

        for st in search_term_split:
            # find direct exact matches:
            if st in item_split:
                direct_finds.setdefault(item, []).append((
                    st,
                    item_split[item_split.index(st)],
                    0,
                ))
            else:
                direct_finds.setdefault(item, []).append((
                    st,
                    None,
                    None,
                ))

            for item_part in item_split:
                # create dist for every st part to every item part
                dist = _calc_distance(
                    st,
                    item_part,
                )
                if dist <= fuzzy_threshold:
                    fuzzy_finds.setdefault(item, []).append((
                        st,
                        item_part,
                        dist,
                    ))

    print(f"direc: {direct_finds}")
    print(f"fuzzy: {fuzzy_finds}")
    unique_results = [(res) for item, res in direct_finds.items()] + [
        (res) for item, res in fuzzy_finds.items()
    ]
    # unique_results = set(direct_finds.keys()).union(set(fuzzy_finds.keys()))
    search_results = unique_results
    #     sts = sorted(search_term_split[search_term])
    #     its = sorted(item_split[item])

    #     max_i = max(
    #         len(sts),
    #         len(its),
    #     )

    #     i = 0
    #     while i < max_i:
    #         search_term_part = sts[i] if i < len(sts) else ""
    #         item_part = its[i] if i < len(its) else ""

    #         i += 1

    #     item_lowered = item.lower()
    #     for st in search_term_split[search_term]:
    #         if st in item_lowered:
    #             # we dont strictly need dist here. used to sort results.
    #             direct_dist = _calc_distance(
    #                 search_term,
    #                 item_lowered,
    #             )
    #             direct_finds[item] = direct_dist
    #             continue
    #     st = None
    #     item_split = dissect_string(item)
    #     # if no direct matches found or param set
    #     # look for off by fuzzy_threshold mistakes
    #     # exclude already found items
    #     if not direct_finds or always_fuzzy:
    #         # TODO: skip prev found items?  and item not in direct_finds
    #         # TODO: skip parts < n chars.
    #         # TODO: benefit comparing only len of search part?

    #         # TODO: make sure all parts are checked on uneven len.

    #         # sort to match words against similar length
    #         sts = sorted(search_term_split[search_term])
    #         its = sorted(item_split[item])
    #         max_i = max(
    #             len(sts),
    #             len(its),
    #         )

    #         i = 0
    #         while i < max_i:
    #             if item in direct_finds:
    #                 break

    #             search_term_part = sts[i] if i < len(sts) else ""
    #             item_part = its[i] if i < len(its) else ""

    #             fuzzy_dist = _calc_distance(
    #                 search_term_part,
    #                 item_part,
    #             )
    #             print(
    #                 f"fuzz: stp: {search_term_part}, itemp: {item_part}, dist: {fuzzy_dist}",
    #             )
    #             # if fuzzy_dist <= fuzzy_threshold + max_threshold_extension:
    #             fuzzy_finds.setdefault(item, []).append(
    #                 fuzzy_dist,
    #             )

    #             i += 1

    # print(f"dir: {direct_finds}")
    # print(f"fuz: {fuzzy_finds}")

    # fuzzy_finds = sorted(
    #     fuzzy_finds.items(),
    #     key=lambda dist: sum(dist[1]),
    # )
    # print(f"fuzs: {fuzzy_finds}")
    # # refine fuzzy results:
    # # findings include all for dist + max_threshold_extension.
    # # this will find "Meister Eder" for "bla", bc Eder-bla dist = 4. So
    # # reduce results to findings with minimal distance by increasing
    # # dist by one up to fuzzy_threshold + max_threshold_extension.
    # # worst case: if eder-bla is the only match, this will be returned.
    # # tbd if useful.
    # closest_fuzzy_find = None
    # exp_step = 0
    # while not closest_fuzzy_find and exp_step <= max_threshold_extension:
    #     # walk all finds until some find with minimal dist.
    #     # expects fuzzy finds sorted.
    #     min_dist = fuzzy_threshold - max_threshold_extension + exp_step
    #     closest_fuzzy_find = [
    #         (find, dist) for find, dist in fuzzy_finds if min(dist) == min_dist
    #     ]
    #     exp_step += 1
    # print(f"clo: {closest_fuzzy_find}")
    # direct_finds = sorted(
    #     direct_finds.items(),
    #     key=lambda dist: dist[1],
    # )

    # search_results.extend(direct_finds)
    # fuzzy_finds_recon = []
    # if closest_fuzzy_find:
    #     # the dist we have for fuzzy is per split item and
    #     # split search term. for accurate return of
    #     # final results, reconstruct dist to complete
    #     # item (and search term?)
    #     # "the bl"-"bla": dist_per_part = 1 (bl[a])
    #     # correct would be dist = 5
    #     # 6 item
    #     # 1 dist
    #     # 3 search
    #     # 5 correct rsult
    #     # (len(item) - dist)
    #     for fuzz_find_item, fuzzy_dist in closest_fuzzy_find:
    #         fuzzy_finds_recon.append((
    #             fuzz_find_item,
    #             min(fuzzy_dist),
    #         ))
    #     # important to append and end bc dist of fuzzy finding are only
    #     # per split search terms vs split item.
    #     search_results.extend(fuzzy_finds_recon)

    # print(f"rec: {fuzzy_finds_recon}")
    return search_results


if __name__ == "__main__":
    db = [
        "berlin mitte",
        "berlin neukölln",
        "berlin",
        "bertin mitte",  # Tippfehler in Teil 1
        "berlin mite",  # Tippfehler in Teil 2
        "münchen mitte",
        "hamburg altona",
        "frankfurt",
        "frankfurt am main",
        "köln",
        "koeln",
        "stuttgart west",
        "the long blanket",
        "blanket",
        "xyz",
    ]

    search_term = "berlin mitte"
    # testsearch = input("seach term: ")
    testsearch = "hutz Eder"
    testthreshold = 5
    results = get_similar(db, search_term, always_fuzzy=True)
    print()
    print(f"search_term: {search_term} ")
    for r in results:
        print(r)
    # for t in db:
    #     print(f"{search_term}, {t}: {_calc_distance(t, testsearch)}")
