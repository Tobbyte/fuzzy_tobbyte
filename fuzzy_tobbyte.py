"""Fuzzy Search implementation using naive Levenshtein algorithm.

Limitations:
    - not optimized in any meaningful way
    - rudimentary sorting order of matches.

Version: 2.1.3

 ~ Made with ❤️ and without ai or code completion (except intelliSense) ~
"""

__all__ = ["get_similar"]  # public method

FUZZY_DIST_DEFAULT = 2
MIN_MATCH_LEN = 2
MID_MATCH_LEN = 5

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


def dissect_string(raw_search_term: str) -> list[str]:
    """Sanitize the users search term.

    Returns a dict of original search term to
    list of lowered and stripped and split on whitespaces.
    """
    return raw_search_term.lower().strip().split()


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
    The fuzzy search only dynamically calculates an allowed distance
    by word length of <= MIN_MATCH_LEN (2) and <= MID_MATCH_LEN (5)
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
        - tbd: require first char the same? tbd.
        - tbd: split on special chars like "-"?
        - return first full match or always fuzzy by param

    """
    search_term_split: list[str] = dissect_string(search_term)
    matches = {}

    for item in db:
        already_matched_st: list[str] = []
        already_matched_ip = []
        item_split = dissect_string(item)

        for st in search_term_split:
            # find direct exact matches:
            allowed_dist = _get_max_allowed_dist(st, fuzzy_threshold)

            if st in item_split:
                matched_word = item_split[item_split.index(st)]
                matches.setdefault(item, []).append((st, matched_word, 0))
                already_matched_st.append(matched_word)

            for i in range(len(item_split)):
                item_part = item_split[i]

                if (
                    item_part not in already_matched_st
                    and item_part not in already_matched_ip
                ):
                    # create dist for every st part to every item part
                    # unless we can exit early bc length diffs
                    if abs(len(st) - len(item_part)) > allowed_dist:
                        continue

                    dist = _calc_distance(st, item_part)
                    if dist <= allowed_dist:
                        matches.setdefault(item, []).insert(
                            i,
                            (st, item_part, dist),
                        )
                        already_matched_ip.append(item_part)

        if set(search_term_split) <= set(already_matched_st) and len(
            search_term_split,
        ) == len(item_split):
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

    # sort by number of matches of split search term to split db item
    # uses num of None matches as scoring factor.
    matches_by_num_of_matches = dict(
        sorted(
            matches.items(),
            key=lambda item: _get_sort_value(item[1], len(search_term_split)),
            reverse=True,
        ),
    )

    # construct table which results have a None before a match
    none_in_front_table = [
        _none_in_res_in_front(res)
        for res in matches_by_num_of_matches.values()
    ]

    matches_by_not_none_in_front = matches_by_num_of_matches

    # move partially matches to the back if their first term not matches
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

    return list(matches_by_not_none_in_front.keys())


def _get_max_allowed_dist(term: str, max_threshold: int) -> int:
    """Calc max allowed distance based on word length."""
    length = len(term)
    if length <= MIN_MATCH_LEN:
        return 0
    if length <= MID_MATCH_LEN:
        return min(1, max_threshold)
    return max_threshold


def _get_sort_value(items_list: list, target_items_count: int) -> float:
    """Rate quality of a match."""
    if None not in items_list:
        factor = 1.1 if len(items_list) == target_items_count else 1
    elif items_list.count(None) == 1:
        factor = 0.9
    else:
        factor = 0.8
    return factor * sum(1 for n in items_list if n is not None)


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
        "hur gggggg cccccc",
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
        "DISNEY MAGIC",
        "A",
        "SAGA",
        "MIR",
        "UMA",
        "MAUD",
        "DISNEY DREAM",
    ]

    # search_term = input("search term: ")
    search_term = "disney mag"
    results = get_similar(db, search_term)
    print(f"\nsearch_term: {search_term} ")
    for r in results:
        print(r)
