from app.utils.auth import generate_room_code, generate_token


def test_token_is_unique():
    tokens = {generate_token() for _ in range(100)}
    assert len(tokens) == 100


def test_room_code_length_and_charset():
    code = generate_room_code()
    assert len(code) == 6
    allowed = set("ABCDEFGHJKLMNPQRSTUVWXYZ23456789")
    assert set(code) <= allowed
