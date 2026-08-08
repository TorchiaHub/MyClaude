from app.origin_guard import MUTATING_METHODS, is_allowed_origin


def test_is_allowed_origin_matches_same_scheme_host_port():
    assert is_allowed_origin(
        "http://127.0.0.1:8000", scheme="http", hostname="127.0.0.1", port=8000
    )


def test_is_allowed_origin_rejects_different_hostname():
    assert not is_allowed_origin(
        "http://evil.example.com:8000", scheme="http", hostname="127.0.0.1", port=8000
    )


def test_is_allowed_origin_rejects_different_port():
    assert not is_allowed_origin(
        "http://127.0.0.1:9999", scheme="http", hostname="127.0.0.1", port=8000
    )


def test_is_allowed_origin_rejects_different_scheme():
    assert not is_allowed_origin(
        "https://127.0.0.1:8000", scheme="http", hostname="127.0.0.1", port=8000
    )


def test_is_allowed_origin_rejects_malformed_origin():
    assert not is_allowed_origin("not-a-url", scheme="http", hostname="127.0.0.1", port=8000)


def test_mutating_methods_covers_state_changing_verbs():
    assert MUTATING_METHODS == {"POST", "PUT", "PATCH", "DELETE"}
    assert "GET" not in MUTATING_METHODS
    assert "HEAD" not in MUTATING_METHODS
    assert "OPTIONS" not in MUTATING_METHODS
