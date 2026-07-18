from app.algorithms.base import OptionInput, VoteInput
from app.algorithms.weighted_random import WeightedRandom


def _opts(n=3):
    return [OptionInput(id=i + 1, text=f"opt{i}", weight=1.0) for i in range(n)]


def test_picks_winner_with_no_votes():
    algo = WeightedRandom()
    result = algo.run(_opts(3), [], num_players=2, seed=1)
    assert result.winner_id in {1, 2, 3}
    assert len(result.eliminated_ids) == 2


def test_eliminate_vote_decreases_weight():
    algo = WeightedRandom()
    votes = [VoteInput(user_id=1, option_id=1, kind="eliminate")]
    result = algo.run(_opts(2), votes, num_players=2, seed=0)
    assert result.winner_id == 2


def test_keep_vote_boosts_weight():
    algo = WeightedRandom()
    votes = [VoteInput(user_id=1, option_id=2, kind="keep")]
    result = algo.run(_opts(2), votes, num_players=2, seed=0)
    assert result.winner_id == 2


def test_dealbreaker_removes_option():
    algo = WeightedRandom()
    votes = [
        VoteInput(user_id=1, option_id=1, is_dealbreaker=True),
        VoteInput(user_id=2, option_id=1, is_dealbreaker=True),
    ]
    result = algo.run(_opts(3), votes, num_players=3, seed=0)
    assert result.winner_id in {2, 3}


def test_seed_determinism():
    algo = WeightedRandom()
    a = algo.run(_opts(5), [], num_players=3, seed=42)
    b = algo.run(_opts(5), [], num_players=3, seed=42)
    assert a.winner_id == b.winner_id


def test_no_options_returns_none():
    algo = WeightedRandom()
    result = algo.run([], [], num_players=0, seed=0)
    assert result.winner_id is None


def test_all_dealbreakered_still_produces_winner():
    algo = WeightedRandom()
    opts = _opts(2)
    votes = [
        VoteInput(user_id=1, option_id=1, is_dealbreaker=True),
        VoteInput(user_id=1, option_id=2, is_dealbreaker=True),
    ]
    result = algo.run(opts, votes, num_players=1, seed=0)
    # Fallback keeps min-vetoed options (both tied → one wins)
    assert result.winner_id in {1, 2}
