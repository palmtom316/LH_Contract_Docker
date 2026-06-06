"""Tests for sync worker startup behavior."""

import run_sync


class DummyScheduler:
    """Minimal scheduler double for startup tests."""

    def __init__(self):
        self.jobs = []
        self.started = False
        self.shutdown_called = False

    def add_job(self, func, trigger, **kwargs):
        self.jobs.append({"func": func, "trigger": trigger, **kwargs})

    def start(self):
        self.started = True

    def shutdown(self):
        self.shutdown_called = True


class DummyLoop:
    """Event loop double that exits immediately."""

    def run_forever(self):
        raise KeyboardInterrupt


def test_main_skips_sync_jobs_when_feishu_config_missing(monkeypatch):
    """Worker should stay idle instead of scheduling broken sync jobs."""
    scheduler = DummyScheduler()

    monkeypatch.delenv("FEISHU_APP_ID", raising=False)
    monkeypatch.delenv("FEISHU_APP_SECRET", raising=False)
    monkeypatch.delenv("FEISHU_BASE_APP_TOKEN", raising=False)
    monkeypatch.delenv("FEISHU_BASE_TABLE_ID", raising=False)
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://test:test@db:5432/test")
    monkeypatch.setattr(run_sync, "AsyncIOScheduler", lambda: scheduler)
    monkeypatch.setattr(run_sync.asyncio, "get_event_loop", lambda: DummyLoop())

    run_sync.main()

    assert scheduler.jobs == []
    assert scheduler.started is True
    assert scheduler.shutdown_called is True
