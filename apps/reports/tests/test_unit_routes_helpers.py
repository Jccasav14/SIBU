from datetime import date

import pytest


def test_cache_key_stable_and_sorted():
    from apps.reports.app.api.routes import _cache_key

    a = _cache_key("x", b=2, a=1)
    b = _cache_key("x", a=1, b=2)
    assert a == b
    assert a.startswith("reports:x|")


def test_window_range_valid_values():
    from apps.reports.app.api.routes import _window_range

    for w in ("24h", "7d", "30d"):
        frm, to = _window_range(w)  # type: ignore[arg-type]
        assert isinstance(frm, date)
        assert isinstance(to, date)
        assert frm <= to


def test_build_cors_origins_expands_localhost():
    from apps.reports.app.main import _build_cors_origins

    out = _build_cors_origins("http://localhost:5173")
    assert "http://localhost:5173" in out
    assert "http://127.0.0.1:5173" in out
