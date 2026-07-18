from app.utils.dealbreaker import apply_dealbreakers


def test_no_dealbreakers_keeps_all():
    assert apply_dealbreakers([1, 2, 3], []) == [1, 2, 3]


def test_single_dealbreaker_removes_one():
    assert apply_dealbreakers([1, 2, 3], [(2, 10)]) == [1, 3]


def test_multiple_dealbreakers_on_same_option_dedup_by_user():
    # same user can't veto same option twice
    result = apply_dealbreakers([1, 2], [(1, 10), (1, 10)])
    assert result == [2]


def test_all_vetoed_falls_back_to_min_count():
    # every option has a veto; option 3 has fewer → it survives
    result = apply_dealbreakers(
        [1, 2, 3],
        [(1, 10), (1, 11), (2, 10), (2, 11), (3, 10)],
    )
    assert result == [3]


def test_all_vetoed_equal_counts_returns_all():
    result = apply_dealbreakers([1, 2], [(1, 10), (2, 11)])
    assert sorted(result) == [1, 2]


def test_empty_options_returns_empty():
    assert apply_dealbreakers([], [(1, 10)]) == []
