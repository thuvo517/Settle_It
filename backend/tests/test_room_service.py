import pytest
from fastapi import HTTPException

from app.state_machine import Phase


def test_create_room_assigns_code_and_host(svc):
    room, host = svc.create_room("Dinner", "iterative_veto", "Alice")
    assert len(room.code) == 6
    assert room.host_id == host.id
    assert host.is_host is True
    assert host.session_token


def test_join_room_allocates_token(svc):
    room, _ = svc.create_room("Dinner", "iterative_veto", "Alice")
    _, bob = svc.join_room(room.code, "Bob")
    assert bob.room_id == room.id
    assert bob.is_host is False
    assert bob.session_token


def test_join_nonexistent_room_404(svc):
    with pytest.raises(HTTPException) as exc:
        svc.join_room("NONE00", "x")
    assert exc.value.status_code == 404


def test_cannot_join_after_start(svc):
    room, _ = svc.create_room("Dinner", "iterative_veto", "Alice")
    svc.transition(room, Phase.SUBMISSION)
    with pytest.raises(HTTPException) as exc:
        svc.join_room(room.code, "Bob")
    assert exc.value.status_code == 409


def test_fuzzy_duplicate_rejected(svc):
    room, alice = svc.create_room("Dinner", "iterative_veto", "Alice")
    svc.transition(room, Phase.SUBMISSION)
    svc.add_option(room, alice, "Pizza Palace")
    with pytest.raises(HTTPException) as exc:
        svc.add_option(room, alice, "pizza  palace!!")
    assert exc.value.status_code == 409


def test_option_limit_per_player(svc):
    room, alice = svc.create_room("Dinner", "iterative_veto", "Alice")
    svc.transition(room, Phase.SUBMISSION)
    names = ["Pizza", "Sushi", "Thai", "Burgers", "Ramen"]
    for name in names:
        svc.add_option(room, alice, name)
    with pytest.raises(HTTPException) as exc:
        svc.add_option(room, alice, "Indian")
    assert exc.value.status_code == 409


def test_cannot_vote_in_submission_phase(svc):
    room, alice = svc.create_room("Dinner", "iterative_veto", "Alice")
    svc.transition(room, Phase.SUBMISSION)
    opt = svc.add_option(room, alice, "Pizza")
    with pytest.raises(HTTPException) as exc:
        svc.cast_vote(room, alice, opt.id, "eliminate", False)
    assert exc.value.status_code == 409


def test_vote_updates_when_recast(svc):
    room, alice = svc.create_room("Dinner", "iterative_veto", "Alice")
    svc.transition(room, Phase.SUBMISSION)
    a = svc.add_option(room, alice, "A")
    b = svc.add_option(room, alice, "B")
    svc.transition(room, Phase.VOTING)
    v1 = svc.cast_vote(room, alice, a.id, "eliminate", False)
    v2 = svc.cast_vote(room, alice, a.id, "keep", True)
    assert v1.id == v2.id
    assert v2.kind == "keep"
    assert v2.is_dealbreaker is True


def test_resolve_picks_winner(svc):
    room, alice = svc.create_room("Dinner", "iterative_veto", "Alice")
    _, bob = svc.join_room(room.code, "Bob")
    svc.transition(room, Phase.SUBMISSION)
    a = svc.add_option(room, alice, "Pizza")
    b = svc.add_option(room, alice, "Sushi")
    svc.transition(room, Phase.VOTING)
    svc.cast_vote(room, alice, a.id, "eliminate", False)
    svc.cast_vote(room, bob, a.id, "eliminate", False)
    svc.cast_vote(room, alice, b.id, "keep", False)
    svc.resolve(room)
    assert room.phase == Phase.RESULTS.value
    assert room.winner_option_id == b.id


def test_reset_clears_state(svc):
    room, alice = svc.create_room("Dinner", "iterative_veto", "Alice")
    svc.transition(room, Phase.SUBMISSION)
    svc.add_option(room, alice, "Pizza")
    svc.transition(room, Phase.LOBBY)
    assert room.phase == Phase.LOBBY.value
    assert len(room.options) == 0


def test_snapshot_shape(svc):
    room, alice = svc.create_room("Dinner", "iterative_veto", "Alice")
    state = svc.snapshot(room)
    assert state.code == room.code
    assert state.phase == "lobby"
    assert len(state.users) == 1
