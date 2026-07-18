from app.algorithms.base import OptionInput, VoteInput
from app.algorithms.iterative_veto import IterativeVeto


def _opts(n):
    return [OptionInput(id=i + 1, text=f"opt{i}", weight=1.0) for i in range(n)]


def test_single_option_wins():
    algo = IterativeVeto()
    result = algo.run(_opts(1), [], num_players=1)
    assert result.winner_id == 1


def test_majority_eliminate_kills_option():
    algo = IterativeVeto()
    # 3 players, option 1 gets 2 eliminate votes (majority) → killed
    votes = [
        VoteInput(user_id=1, option_id=1, kind="eliminate"),
        VoteInput(user_id=2, option_id=1, kind="eliminate"),
        VoteInput(user_id=1, option_id=2, kind="keep"),
    ]
    result = algo.run(_opts(2), votes, num_players=3)
    assert result.winner_id == 2


def test_low_keep_eliminated_when_no_majority():
    algo = IterativeVeto()
    # Nobody eliminates; option 2 has zero keeps → it dies first,
    # then option 1 wins since no more options remain.
    votes = [VoteInput(user_id=1, option_id=1, kind="keep")]
    result = algo.run(_opts(2), votes, num_players=3)
    assert result.winner_id == 1


def test_dealbreaker_eliminates_option():
    algo = IterativeVeto()
    votes = [VoteInput(user_id=1, option_id=1, is_dealbreaker=True)]
    result = algo.run(_opts(2), votes, num_players=2)
    assert result.winner_id == 2


def test_converges_without_votes():
    algo = IterativeVeto()
    result = algo.run(_opts(4), [], num_players=2)
    assert result.winner_id is not None
    assert len(result.eliminated_ids) == 3


def test_records_rounds_trace():
    algo = IterativeVeto()
    result = algo.run(_opts(3), [], num_players=2)
    assert result.trace  # non-empty trace
