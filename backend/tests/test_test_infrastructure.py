"""
Tests for pytest infrastructure helpers.
"""
import pytest

from tests import conftest as test_conftest


def test_database_fixture_skips_when_postgres_is_unavailable(monkeypatch):
    def _raise_unavailable():
        raise PermissionError(1, "Operation not permitted")

    monkeypatch.setattr(test_conftest, "_ensure_postgres_test_database", _raise_unavailable)

    with pytest.raises(pytest.skip.Exception, match="PostgreSQL test database unavailable"):
        test_conftest._ensure_postgres_test_database_or_skip(event_loop=None)
