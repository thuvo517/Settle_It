from app.utils.fuzzy import find_duplicate, normalize, similarity


def test_normalize_strips_case_and_punctuation():
    assert normalize("  Hello, World!!  ") == "hello world"


def test_normalize_collapses_whitespace():
    assert normalize("pizza\n\tplace") == "pizza place"


def test_normalize_handles_unicode():
    assert normalize("Café") == "cafe"


def test_similarity_identical_is_100():
    assert similarity("pizza place", "pizza place") == 100


def test_similarity_distinct_is_low():
    assert similarity("pizza", "rollerblading") < 50


def test_find_duplicate_detects_near_match():
    existing = [normalize("Pizza Palace"), normalize("Sushi Den")]
    dup = find_duplicate(normalize("pizza  palace!!"), existing, threshold=85)
    assert dup == normalize("Pizza Palace")


def test_find_duplicate_returns_none_when_below_threshold():
    existing = [normalize("Pizza Palace")]
    assert find_duplicate(normalize("Thai Kitchen"), existing, threshold=85) is None


def test_find_duplicate_handles_word_reorder():
    existing = [normalize("hot spicy wings")]
    assert find_duplicate(normalize("spicy hot wings"), existing, threshold=85) is not None
