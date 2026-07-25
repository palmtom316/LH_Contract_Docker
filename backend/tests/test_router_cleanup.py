from pathlib import Path


def test_system_router_keeps_authoritative_reset_endpoint():
    backend_root = Path(__file__).resolve().parents[1]
    system_router = backend_root / "app/routers/system.py"
    content = system_router.read_text(encoding="utf-8")

    assert '@router.post("/reset")' in content
    assert "async def reset_system" in content
    assert "SystemResetRequest" in content
    assert "verify_password(reset_request.password" in content
    assert "if not settings.DEBUG" in content
    assert "reset_request.dry_run" in content
    assert "create_audit_log" in content


def test_finance_import_worker_only_runs_in_standalone_worker():
    backend_root = Path(__file__).resolve().parents[1]
    main_content = (backend_root / "app/main.py").read_text(encoding="utf-8")
    worker_content = (backend_root / "run_sync.py").read_text(encoding="utf-8")

    assert "run_finance_import_worker" not in main_content
    assert "async def run_finance_import_worker" in worker_content
    assert "claim_next_batch" in worker_content


def test_backend_router_directory_has_no_orphaned_reset_snippet():
    backend_root = Path(__file__).resolve().parents[1]
    orphaned_snippet = backend_root / "app/routers/system_reset_snippet.py"

    assert not orphaned_snippet.exists()
