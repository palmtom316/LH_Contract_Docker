"""Regression tests for database session compatibility exports."""


def test_database_module_exports_async_session_alias():
    """Legacy Feishu code still imports async_session from app.database."""
    from app.database import AsyncSessionLocal, async_session

    assert async_session is AsyncSessionLocal
