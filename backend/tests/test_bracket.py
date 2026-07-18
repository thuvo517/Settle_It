from app.algorithms.base import OptionInput, VoteInput
from app.algorithms.bracket import Bracket


def _opts(n):
    return [OptionInput(id=i + 1, text=f"opt{i}", weight=1.0) for i in range(n)]


def test_single_option_wins_outright():
    algo = Bracket()
    result = algo.run(_opts(1), [], num_players=1)
    assert result.winner_id == 1


def test_bracket_power_of_two():
    algo = Bracket()
    votes = [
        VoteInput(user_id=1, option_id=1, kind="keep"),
        VoteInput(user_id=2, option_id=3, kind="keep"),
    ]
    result = algo.run(_opts(4), votes, num_players=2)
    assert result.winner_id is not None
    assert len(result.eliminated_ids) == 3


def test_bracket_with_bye():
    algo = Bracket()
    # 3 options → one bye; clear keep on option 2 should promote it
    votes = [VoteInput(user_id=1, option_id=2, kind="keep")]
    result = algo.run(_opts(3), votes, num_players=1)
    assert result.winner_id is not None


def test_bracket_dealbreaker_removes_option():
    algo = Bracket()
    votes = [VoteInput(user_id=1, option_id=1, is_dealbreaker=True)]
    result = algo.run(_opts(2), votes, num_players=1)
    assert result.winner_id == 2


def test_bracket_net_votes_decide_pair():
    algo = Bracket()
    # Keep votes on 1 vs eliminate on 2 → 1 advances
    votes = [
        VoteInput(user_id=1, option_id=1, kind="keep"),
        VoteInput(user_id=2, option_id=2, kind="eliminate"),
    ]
    result = algo.run(_opts(2), votes, num_players=2)
    assert result.winner_id == 1


def test_bracket_rounds_logged():
    algo = Bracket()
    result = algo.run(_opts(4), [], num_players=2)
    assert any("pairings" in r for r in result.rounds)
