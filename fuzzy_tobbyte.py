"""Fuzzy Search implementation using naive Levenshtein algorithm.

Limitations:
    - not optimized in any meaningful way
    - rudimentary sorting order of matches.

Version: 2.1.1

 ~ Made with ❤️ and without ai or code completion (except intelliSense) ~
"""

__all__ = ["get_similar"]  # public method

FUZZY_DIST_DEFAULT = 2


def _calc_distance(
    search_term: str,
    compar_term: str,
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
    fuzzy_threshold: int = FUZZY_DIST_DEFAULT,
) -> list[str]:
    """Return similar words.

    Does not consider capitalization.
    Looks for direct matches and fuzzy matches of any part of the search
    term in any part of the db items.
    Returns full, direct matches directly and stops searching further.
    The fuzzy search only considers parts of the db items in the length
    of the length of the original search term parts to better match
    small typos.
    Can take multi part search terms and or db items. Both get lowered
    for comparison and stripped off and by whitespaces.
    Does not sanitize by any other means.
    Sorts findings by number of matches, prioritizes matches where first
    parts of query and results match.

    Args:
        db (list[str]): The items to be searched.
        search_term (str): The search term to be looked for.
        fuzzy_threshold (int): The max distance to count as match.

    Returns:
        list[str]: List of db items that are similar to the search term.

    Todo:
        - export sort by total / avg by param
        - exclude words of matching when
            len(word) == FUZZY_DIST_DEFAULT (+ x ?). So that no longer
            "ab" matches "cd". require first char the same? tbd.
        - tbd: split on special chars like "-"?
        - return first full match or always fuzzy by param

    """
    search_term_split: list[str] = dissect_string(search_term)[search_term]
    matches = {}
    already_matched_st: list[str] = []
    already_matched_ip = []

    for item in db:
        item_split = dissect_string(item)[item]

        for st in search_term_split:
            # find direct exact matches:
            if st in item_split:
                matches.setdefault(item, []).append((
                    st,
                    item_split[item_split.index(st)],
                    0,
                ))
                already_matched_st.append(item_split[item_split.index(st)])

            for i in range(len(item_split)):
                item_part = item_split[i]
                # create dist for every st part to every item part
                if item_part not in already_matched_st:
                    dist = _calc_distance(
                        st,
                        item_part,
                    )
                    if dist <= fuzzy_threshold:
                        matches.setdefault(item, []).insert(
                            i,
                            (
                                st,
                                item_part,
                                dist,
                            ),
                        )
                        already_matched_ip.append(item_part)

        if set(search_term_split) <= set(already_matched_st):
            # all search term parts matched directly db item.
            # no need to look further (except flag thats tbd.)
            return [item]

        # fill with Nones for item_parts not matched direct or fuzzy.
        # Used for sorting order of results.
        for i in range(len(item_split)):
            item_part = item_split[i]
            if (
                item in matches
                and item_part not in already_matched_st
                and item_part not in already_matched_ip
            ):
                matches[item].insert(i, None)

    # now we have:
    # dict[str, list[tuple | None]] :
    #     - where len(list) is len(db_item.split())
    #     - list items are:
    #         - for no match of db_item part (ip)
    #           to search_term part (sp): "None",
    #         - for matches of ip and sp: "(sp, ip, dist)"
    #     f.e. db_item "münchen mitte" and search_term "berlin mitte":
    #     returns {"münchen mitte": [None, ('mitte', 'mite', 1)]}

    # sort to weight order of results ascending:
    # multiple matches direct                           ✓
    # multiple matches fuzzy                            ✓
    # partial matches where first terms match           ✓
    # partial matches where first terms NOT matches     ✓
    # sort by dist (total or average of distances):     ✓

    # sort by number of matches of split search term to split db item
    matches_by_num_of_matches = dict(
        sorted(
            matches.items(),
            key=lambda item: sum(1 for n in item[1] if n is not None),
            reverse=True,
        ),
    )

    # construct table which results have a None before a match
    none_in_front_table = [
        _none_in_res_in_front(res)
        for res in matches_by_num_of_matches.values()
    ]

    matches_by_not_none_in_front = matches_by_num_of_matches

    # move partially matches where first term not matches to the back
    if none_in_front_table:
        paired = list(
            zip(
                matches_by_not_none_in_front.items(),
                none_in_front_table,
                strict=False,
            ),
        )
        paired.sort(key=lambda x: x[1])  # False < True
        matches_by_not_none_in_front = dict(k for k, v in paired)

    # sort by average distance of (partial) matches
    sorted_by_distance = dict(
        sorted(
            matches_by_not_none_in_front.items(),
            # key=lambda item: total_distance(item[1]),
            key=lambda item: avg_distance(item[1]),
        ),
    )

    return list(sorted_by_distance.keys())


def avg_distance(matches: list) -> float:
    """Calculate the average distance of matches."""
    dists = [m[2] for m in matches if m is not None]
    return sum(dists) / len(dists) if dists else float("inf")


def total_distance(matches: list) -> int:
    """Calculate the total distance of matches."""
    return sum(m[2] for m in matches if m is not None)


def _none_in_res_in_front(li: list) -> bool:
    """Check if a None is in front of a not-None in a List."""
    if None in li:
        none_i = li.index(None)
        for i in range(len(li)):
            item = li[i]
            if item is not None and i < none_i:  # noqa: SIM103
                return False
            return True
    return False


if __name__ == "__main__":
    db = [
        "HMS QUEEN ELIZABETH",
        "hurtz berlin mitte",
        "münchen mite",
        "berlin neukölln",
        "berlin",
        "bertin mitte",
        "USS Theodore Rooseve",
        "berlin mite",
        "hamburg altona",
        "frankfurt",
        "frankfurt am main",
        "ussu",
        "köln",
        "koeln",
        "stuttgart west",
        "the long blanket",
        "blanket",
        "xyz",
    ]

    # search_term = "berlin mitte"
    search_term = input("search term: ")
    results = get_similar(db, search_term)
    print(f"\nsearch_term: {search_term} ")
    for r in results:
        print(r)
