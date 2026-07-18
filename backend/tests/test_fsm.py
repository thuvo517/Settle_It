import pytest

from app.state_machine import IllegalTransition, Phase, RoomFSM


def test_initial_phase_is_lobby():
    assert RoomFSM().phase is Phase.LOBBY


def test_lobby_to_submission_allowed():
    fsm = RoomFSM()
    fsm.transition(Phase.SUBMISSION)
    assert fsm.phase is Phase.SUBMISSION


def test_lobby_to_voting_not_allowed():
    fsm = RoomFSM()
    with pytest.raises(IllegalTransition):
        fsm.transition(Phase.VOTING)


def test_submission_to_voting_allowed():
    fsm = RoomFSM(Phase.SUBMISSION)
    fsm.transition(Phase.VOTING)
    assert fsm.phase is Phase.VOTING


def test_voting_to_results_allowed():
    fsm = RoomFSM(Phase.VOTING)
    fsm.transition(Phase.RESULTS)
    assert fsm.phase is Phase.RESULTS


def test_results_can_reset_to_lobby():
    fsm = RoomFSM(Phase.RESULTS)
    fsm.transition(Phase.LOBBY)
    assert fsm.phase is Phase.LOBBY


def test_results_cannot_skip_back_to_voting():
    fsm = RoomFSM(Phase.RESULTS)
    with pytest.raises(IllegalTransition):
        fsm.transition(Phase.VOTING)


def test_submission_can_abort_to_lobby():
    fsm = RoomFSM(Phase.SUBMISSION)
    fsm.transition(Phase.LOBBY)
    assert fsm.phase is Phase.LOBBY


def test_from_str_roundtrip():
    fsm = RoomFSM.from_str("voting")
    assert fsm.phase is Phase.VOTING
